from app.core.exceptions import (
    ConsultaNaoEncontradaError,
    ErroNavegacaoError,
    TimeoutConsultaError,
)


def test_consulta_nao_encontrada_mensagem() -> None:
    exc = ConsultaNaoEncontradaError("João Silva", "NOME")
    assert "João Silva" in str(exc)
    assert exc.termo == "João Silva"
    assert exc.tipo == "NOME"


def test_timeout_consulta_mensagem_padrao() -> None:
    exc = TimeoutConsultaError()
    assert "tempo de resposta" in exc.mensagem


def test_timeout_consulta_com_identificador() -> None:
    exc = TimeoutConsultaError("12345")
    assert "tempo de resposta" in exc.mensagem


def test_erro_navegacao_detalhe() -> None:
    exc = ErroNavegacaoError("elemento não encontrado")
    assert "elemento não encontrado" in exc.detalhe
    assert "navegação" in str(exc)
