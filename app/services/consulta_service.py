import logging

from app.bot.browser import BrowserManager
from app.bot.scraper import TransparenciaScraper
from app.core.exceptions import (
    ConsultaNaoEncontradaException,
    ErroNavegacaoException,
    TimeoutConsultaException,
)
from app.models.request import ConsultaRequest, TipoIdentificador
from app.models.response import ConsultaResponse

logger = logging.getLogger(__name__)


class ConsultaService:
    """
    Orquestra a consulta ao Portal da Transparência.
    Instancia BrowserManager e TransparenciaScraper por execução,
    garantindo isolamento total entre requisições simultâneas.
    """

    async def executar(self, request: ConsultaRequest) -> ConsultaResponse:
        """
        Executa uma consulta e retorna resposta padronizada.

        Todos os cenários de erro são capturados e mapeados para
        ConsultaResponse com sucesso=False e mensagem_erro preenchida.
        """
        # Nunca logar CPF/NIS em produção
        tipo_log = request.tipo.value
        if request.tipo == TipoIdentificador.NOME:
            logger.info("Iniciando consulta por NOME")
        else:
            logger.info("Iniciando consulta por %s", tipo_log)

        try:
            async with BrowserManager() as mgr:
                scraper = TransparenciaScraper(mgr.page)
                return await scraper.consultar(
                    identificador=request.identificador,
                    tipo=request.tipo,
                    filtro_social=request.filtro_social,
                )

        except ConsultaNaoEncontradaException as exc:
            logger.info("Consulta não encontrada: tipo=%s", tipo_log)
            return ConsultaResponse(
                sucesso=False,
                mensagem_erro=(
                    f"Foram encontrados 0 resultados para o termo {exc.termo}"
                ),
            )

        except TimeoutConsultaException as exc:
            logger.warning("Timeout na consulta: tipo=%s", tipo_log)
            return ConsultaResponse(
                sucesso=False,
                mensagem_erro=exc.mensagem,
            )

        except ErroNavegacaoException as exc:
            logger.error("Erro de navegação: %s", exc.detalhe)
            return ConsultaResponse(
                sucesso=False,
                mensagem_erro=f"Erro durante a navegação: {exc.detalhe}",
            )

        except Exception as exc:
            logger.exception("Erro inesperado no ConsultaService")
            return ConsultaResponse(
                sucesso=False,
                mensagem_erro=f"Erro interno inesperado: {type(exc).__name__}",
            )
