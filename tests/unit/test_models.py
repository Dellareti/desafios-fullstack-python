import pytest
from pydantic import ValidationError

from app.models.request import ConsultaRequest, TipoIdentificador
from app.models.response import BeneficioDetalhe, ConsultaResponse


class TestConsultaRequest:
    def test_request_cpf_valido(self) -> None:
        req = ConsultaRequest(
            identificador="123.456.789-00", tipo=TipoIdentificador.CPF
        )
        assert req.tipo == TipoIdentificador.CPF
        assert req.filtro_social is False

    def test_request_nome_com_filtro(self) -> None:
        req = ConsultaRequest(
            identificador="João Silva",
            tipo=TipoIdentificador.NOME,
            filtro_social=True,
        )
        assert req.filtro_social is True

    def test_request_identificador_vazio_invalido(self) -> None:
        with pytest.raises(ValidationError):
            ConsultaRequest(identificador="", tipo=TipoIdentificador.CPF)

    def test_request_tipo_invalido(self) -> None:
        with pytest.raises(ValidationError):
            ConsultaRequest(identificador="123", tipo="INVALIDO")  # type: ignore[arg-type]


class TestConsultaResponse:
    def test_response_sucesso(self) -> None:
        resp = ConsultaResponse(sucesso=True, nome="João da Silva")
        assert resp.sucesso is True
        assert resp.mensagem_erro is None
        assert resp.beneficios == []

    def test_response_erro(self) -> None:
        resp = ConsultaResponse(sucesso=False, mensagem_erro="Não encontrado")
        assert resp.sucesso is False
        assert resp.mensagem_erro == "Não encontrado"

    def test_beneficio_detalhe(self) -> None:
        b = BeneficioDetalhe(
            nome_beneficio="Bolsa Família",
            competencia="01/2024",
            valor=600.0,
            situacao="Pago",
        )
        assert b.valor == 600.0
