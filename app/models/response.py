from datetime import UTC, datetime

from pydantic import BaseModel, Field


class BeneficioDetalhe(BaseModel):
    """Detalhe de um benefício social recebido."""

    nome_beneficio: str = Field(
        ..., description="Nome do benefício (ex: Bolsa Família)"
    )  # noqa: E501
    competencia: str = Field(..., description="Mês/ano de competência (ex: 01/2024)")
    valor: float = Field(..., description="Valor do benefício em reais")
    situacao: str = Field(
        ..., description="Situação do benefício (ex: Pago, Cancelado)"
    )  # noqa: E501


class ConsultaResponse(BaseModel):
    """Modelo de resposta da consulta no Portal da Transparência."""

    sucesso: bool = Field(..., description="Indica se a consulta foi bem-sucedida")
    mensagem_erro: str | None = Field(
        default=None,
        description="Mensagem de erro em caso de falha",
    )
    nome: str | None = Field(default=None, description="Nome completo da pessoa")
    cpf: str | None = Field(
        default=None, description="CPF mascarado (ex: ***.456.789-**)"
    )  # noqa: E501
    nis: str | None = Field(default=None, description="NIS da pessoa")
    data_nascimento: str | None = Field(
        default=None,
        description="Data de nascimento no formato ISO 8601 (YYYY-MM-DD)",
    )
    municipio_uf: str | None = Field(
        default=None,
        description="Município e UF de domicílio (ex: São Paulo/SP)",
    )
    beneficios: list[BeneficioDetalhe] = Field(
        default_factory=list,
        description="Lista de benefícios sociais encontrados",
    )
    screenshot_base64: str | None = Field(
        default=None,
        description="Screenshot da página em Base64 (PNG)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp da consulta em UTC",
    )
