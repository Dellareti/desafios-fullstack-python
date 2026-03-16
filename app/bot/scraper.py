import base64
import logging

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.bot.parser import (
    limpar_texto,
    parse_valor_monetario,
)
from app.core.config import settings
from app.core.exceptions import (
    ConsultaNaoEncontradaError,
    ErroNavegacaoError,
    TimeoutConsultaError,
)
from app.models.request import TipoIdentificador
from app.models.response import BeneficioDetalhe, ConsultaResponse

logger = logging.getLogger(__name__)

_BASE_URL = "https://portaldatransparencia.gov.br/pessoa-fisica/busca/lista"
_DETALHE_URL_PREFIX = "/busca/pessoa-fisica/"

# Nomes de benefícios exatamente como aparecem no portal (strong tags)
_BENEFICIOS_CONHECIDOS = [
    "Bolsa Família",
    "Auxílio Brasil",
    "Auxílio Emergencial",
    "BPC",
    "Seguro Desemprego",
    "Abono Salarial",
]

# JS que extrai dados da seção .dados-tabelados
_JS_EXTRAIR_DADOS = """
() => {
    const section = document.querySelector('section.dados-tabelados');
    if (!section) return {};
    const dados = {};
    section.querySelectorAll('strong').forEach(strong => {
        const label = strong.textContent.trim();
        let el = strong.nextElementSibling;
        while (el && el.tagName !== 'SPAN') {
            el = el.nextElementSibling;
        }
        if (el) {
            dados[label] = el.textContent.trim();
        }
    });
    return dados;
}
"""

# JS que extrai todos os benefícios do accordion
_JS_EXTRAIR_BENEFICIOS = """
() => {
    const accordion = document.querySelector('#accordion-recebimentos-recursos');
    if (!accordion) return [];
    const resultado = [];
    const strongs = accordion.querySelectorAll('strong');
    strongs.forEach(strong => {
        const nome = strong.textContent.trim();
        let sibling = strong.nextElementSibling;
        while (sibling && sibling.tagName !== 'TABLE') {
            sibling = sibling.nextElementSibling;
        }
        if (!sibling) return;
        const rows = sibling.querySelectorAll('tbody tr');
        rows.forEach(tr => {
            const tds = tr.querySelectorAll('td');
            if (tds.length < 4) return;
            // col 0: Detalhar | col 1: NIS | col 2: Nome | col 3: Valor Recebido
            const nis = tds[1].textContent.trim();
            const valor = tds[3].textContent.trim();
            resultado.push({ nome_beneficio: nome, nis: nis, valor_txt: valor });
        });
    });
    return resultado;
}
"""


class TransparenciaScraper:
    """
    Executa o fluxo completo de consulta no Portal da Transparência.
    Recebe uma Page do Playwright já inicializada — sem estado global.
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    async def consultar(
        self,
        identificador: str,
        tipo: TipoIdentificador,
        filtro_social: bool = False,
    ) -> ConsultaResponse:
        """
        Executa a consulta completa e retorna o resultado estruturado.

        Raises:
            ConsultaNaoEncontradaError: Nenhum resultado encontrado.
            TimeoutConsultaError: Tempo limite excedido.
            ErroNavegacaoError: Erro inesperado durante a navegação.
        """
        try:
            await self._navegar_para_busca(identificador, filtro_social)
            ja_na_pagina_detalhe = await self._aguardar_resultados(identificador, tipo)

            if not ja_na_pagina_detalhe:
                await self._clicar_primeiro_resultado(identificador, tipo)

            dados_pessoa = await self._extrair_dados_pessoa()
            screenshot = await self._capturar_screenshot()
            beneficios = await self._coletar_beneficios(dados_pessoa)

            # NIS pode vir do accordion; remover do dict intermediário
            nis = dados_pessoa.pop("_nis_accordion", None)
            if not dados_pessoa.get("nis"):
                dados_pessoa["nis"] = nis

            return ConsultaResponse(
                sucesso=True,
                **dados_pessoa,
                beneficios=beneficios,
                screenshot_base64=screenshot,
            )

        except ConsultaNaoEncontradaError:
            raise
        except TimeoutConsultaError:
            raise
        except PlaywrightTimeoutError as exc:
            logger.warning("Timeout Playwright: %s", exc)
            raise TimeoutConsultaError() from exc
        except Exception as exc:
            logger.exception("Erro inesperado durante scraping")
            raise ErroNavegacaoError(str(exc)) from exc

    async def _navegar_para_busca(
        self,
        identificador: str,
        filtro_social: bool,
    ) -> None:
        """Navega até a página de busca e preenche o formulário."""
        logger.info("Navegando para o Portal da Transparência")
        await self._page.goto(_BASE_URL, wait_until="domcontentloaded")
        await self._page.wait_for_selector("#termo", timeout=15_000)

        # Campo de busca real: id="termo"
        await self._page.fill("#termo", identificador)

        # Filtro social: id="beneficiarioProgramaSocial"
        if filtro_social:
            try:
                await self._page.check("#beneficiarioProgramaSocial", timeout=5_000)
                logger.debug("Filtro social ativado")
            except Exception:
                logger.debug("Checkbox filtro social não disponível")

        # Submeter via Enter (botão está fora do viewport)
        await self._page.press("#termo", "Enter")

    async def _aguardar_resultados(
        self,
        identificador: str,
        tipo: TipoIdentificador,
    ) -> bool:
        """
        Aguarda carregamento e verifica resultados.
        Retorna True se já estiver na página de detalhe (CPF/NIS com match direto).
        """
        try:
            await self._page.wait_for_load_state(
                "networkidle", timeout=settings.timeout_ms
            )
        except PlaywrightTimeoutError:
            raise TimeoutConsultaError(identificador)

        url_atual = self._page.url

        # Portal redirecionou direto para o detalhe (CPF/NIS único)
        if _DETALHE_URL_PREFIX in url_atual:
            logger.debug("Redirecionado diretamente para página de detalhe")
            return True

        # Verificar contador de resultados: <strong id="countResultados">N</strong>
        count_el = self._page.locator("#countResultados")
        if await count_el.count() > 0:
            count_txt = limpar_texto(await count_el.inner_text())
            if count_txt == "0":
                raise ConsultaNaoEncontradaError(identificador, tipo.value)
            logger.debug("Resultados encontrados: %s", count_txt)
            return False

        # Fallback: texto da página
        body_txt = await self._page.inner_text("body")
        body_lower = body_txt.lower()
        if (
            "foram encontrados 0 resultados" in body_lower
            or "nenhum resultado" in body_lower
        ):
            raise ConsultaNaoEncontradaError(identificador, tipo.value)

        if "não foi possível" in body_lower and tipo != TipoIdentificador.NOME:
            raise TimeoutConsultaError(identificador)

        return False

    async def _clicar_primeiro_resultado(
        self,
        identificador: str,
        tipo: TipoIdentificador,
    ) -> None:
        """Clica no primeiro link .link-busca-nome da lista de resultados."""
        # Seletor real do portal: <a class="link-busca-nome" href="...">NOME</a>
        primeiro_link = self._page.locator("a.link-busca-nome").first
        if await primeiro_link.count() == 0:
            raise ConsultaNaoEncontradaError(identificador, tipo.value)

        await primeiro_link.click()
        await self._page.wait_for_load_state("networkidle", timeout=settings.timeout_ms)

    async def _extrair_dados_pessoa(self) -> dict[str, str | None]:
        """
        Extrai dados da seção .dados-tabelados via JavaScript.
        Estrutura real: <strong>LABEL</strong><span>VALOR</span>
        """
        dados_raw: dict[str, str] = await self._page.evaluate(_JS_EXTRAIR_DADOS)

        return {
            "nome": dados_raw.get("Nome") or None,
            "cpf": dados_raw.get("CPF") or None,
            "nis": dados_raw.get("NIS") or None,
            "data_nascimento": dados_raw.get("Data de Nascimento") or None,
            # Portal usa "Localidade" (ex: "CAXIAS DO SUL - RS")
            "municipio_uf": (
                dados_raw.get("Localidade") or dados_raw.get("Município") or None
            ),
            "_nis_accordion": None,  # preenchido por _coletar_beneficios
        }

    async def _capturar_screenshot(self) -> str:
        """Captura screenshot da página inteira e retorna como Base64."""
        logger.debug("Capturando screenshot")
        screenshot_bytes = await self._page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def _coletar_beneficios(
        self, dados_pessoa: dict[str, str | None]
    ) -> list[BeneficioDetalhe]:
        """
        Coleta benefícios do accordion de Recebimentos sem navegar para outra página
        (páginas de detalhe exigem CAPTCHA).

        Estrutura real do portal:
          <strong>Auxílio Emergencial</strong>
          <table>
            <thead><tr><th>Detalhar</th><th>NIS</th><th>Nome</th>
                        <th>Valor Recebido</th></tr></thead>
            <tbody><tr><td>[btn]</td><td>NIS</td><td>NOME</td>
                        <td>R$ X,XX</td></tr></tbody>
          </table>
        """
        # Tentar expandir accordion se estiver fechado
        try:
            btn_accordion = self._page.locator(
                'button.header[aria-controls="accordion-recebimentos-recursos"]'
            )
            if await btn_accordion.count() > 0:
                await btn_accordion.click()
                await self._page.wait_for_timeout(800)
        except Exception:
            pass

        raw: list[dict[str, str]] = await self._page.evaluate(_JS_EXTRAIR_BENEFICIOS)
        beneficios: list[BeneficioDetalhe] = []
        nis_extraido: str | None = None

        for item in raw:
            nome_beneficio = item.get("nome_beneficio", "")
            if nome_beneficio not in _BENEFICIOS_CONHECIDOS:
                continue

            valor = parse_valor_monetario(item.get("valor_txt", ""))
            nis_item = item.get("nis", "").strip()
            if nis_item and not nis_extraido:
                nis_extraido = nis_item

            beneficios.append(
                BeneficioDetalhe(
                    nome_beneficio=nome_beneficio,
                    competencia="N/D",  # resumo não expõe competência
                    valor=valor,
                    situacao="Recebido",
                )
            )
            logger.debug("Benefício extraído: %s R$ %.2f", nome_beneficio, valor)

        # Propagar NIS encontrado no accordion de volta para dados_pessoa
        if nis_extraido:
            dados_pessoa["_nis_accordion"] = nis_extraido

        return beneficios
