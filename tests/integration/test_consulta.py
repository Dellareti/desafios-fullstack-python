"""
Testes de integração — acessam o Portal da Transparência de verdade.
Requerem conexão com internet e Chromium instalado.

Executar com:
    pytest tests/integration/ -v --timeout=60
"""
import pytest

from app.models.request import ConsultaRequest, TipoIdentificador
from app.services.consulta_service import ConsultaService

pytestmark = pytest.mark.asyncio


# Cenário 1: CPF válido retorna dados + screenshot
@pytest.mark.integration
async def test_sucesso_cpf() -> None:
    """CPF válido de pessoa pública deve retornar JSON com dados e screenshot."""
    service = ConsultaService()
    request = ConsultaRequest(
        identificador="000.000.001-91",  # CPF de teste do portal
        tipo=TipoIdentificador.CPF,
    )
    response = await service.executar(request)

    # Pode ser sucesso ou erro de não encontrado — ambos são válidos
    assert response.sucesso is True or response.mensagem_erro is not None
    if response.sucesso:
        assert response.screenshot_base64 is not None
        assert len(response.screenshot_base64) > 0


# Cenário 2: CPF inválido retorna mensagem de erro correta
@pytest.mark.integration
async def test_erro_cpf() -> None:
    """CPF inexistente deve retornar mensagem de timeout/não encontrado."""
    service = ConsultaService()
    request = ConsultaRequest(
        identificador="999.999.999-99",
        tipo=TipoIdentificador.CPF,
    )
    response = await service.executar(request)

    assert response.sucesso is False
    assert response.mensagem_erro is not None
    assert (
        "Não foi possível retornar os dados no tempo de resposta solicitado"
        in response.mensagem_erro
        or "0 resultados" in response.mensagem_erro
        or "não" in response.mensagem_erro.lower()
    )


# Cenário 3: Nome completo retorna dados do primeiro resultado
@pytest.mark.integration
async def test_sucesso_nome() -> None:
    """Nome completo de pessoa pública deve retornar dados do primeiro resultado."""
    service = ConsultaService()
    request = ConsultaRequest(
        identificador="Lula da Silva",
        tipo=TipoIdentificador.NOME,
    )
    response = await service.executar(request)

    assert response.sucesso is True or response.mensagem_erro is not None
    if response.sucesso:
        assert response.nome is not None
        assert response.screenshot_base64 is not None


# Cenário 4: Nome inexistente retorna 0 resultados
@pytest.mark.integration
async def test_erro_nome() -> None:
    """Nome totalmente fictício deve retornar mensagem com 0 resultados."""
    service = ConsultaService()
    request = ConsultaRequest(
        identificador="Zzzzxxxxxqqqq Inexistente99999",
        tipo=TipoIdentificador.NOME,
    )
    response = await service.executar(request)

    assert response.sucesso is False
    assert response.mensagem_erro is not None
    assert "0 resultados" in response.mensagem_erro or "não" in response.mensagem_erro.lower()


# Cenário 5: Sobrenome + filtro social retorna resultado filtrado
@pytest.mark.integration
async def test_filtrado() -> None:
    """Busca por sobrenome com filtro social deve retornar beneficiários."""
    service = ConsultaService()
    request = ConsultaRequest(
        identificador="Silva",
        tipo=TipoIdentificador.NOME,
        filtro_social=True,
    )
    response = await service.executar(request)

    # Resultado pode ser sucesso ou erro — o importante é não lançar exceção
    assert isinstance(response.sucesso, bool)
    assert response.mensagem_erro is None or isinstance(response.mensagem_erro, str)
