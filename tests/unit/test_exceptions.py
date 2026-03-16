from app.core.exceptions import (
    ConsultaNaoEncontradaException,
    ErroNavegacaoException,
    TimeoutConsultaException,
)


def test_consulta_nao_encontrada_mensagem() -> None:
    exc = ConsultaNaoEncontradaException("João Silva", "NOME")
    assert "João Silva" in str(exc)
    assert exc.termo == "João Silva"
    assert exc.tipo == "NOME"


def test_timeout_consulta_mensagem_padrao() -> None:
    exc = TimeoutConsultaException()
    assert "tempo de resposta" in exc.mensagem


def test_timeout_consulta_com_identificador() -> None:
    exc = TimeoutConsultaException("12345")
    assert "tempo de resposta" in exc.mensagem


def test_erro_navegacao_detalhe() -> None:
    exc = ErroNavegacaoException("elemento não encontrado")
    assert "elemento não encontrado" in exc.detalhe
    assert "navegação" in str(exc)
