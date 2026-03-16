from enum import Enum

from pydantic import BaseModel, Field


class TipoIdentificador(str, Enum):
    """Tipo de identificador para a consulta."""

    CPF = "CPF"
    NIS = "NIS"
    NOME = "NOME"


class ConsultaRequest(BaseModel):
    """Modelo de entrada para consulta no Portal da Transparência."""

    identificador: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="CPF, NIS ou nome da pessoa a ser consultada",
        examples=["123.456.789-00", "12345678900", "João da Silva"],
    )
    tipo: TipoIdentificador = Field(
        ...,
        description="Tipo de identificador: CPF, NIS ou NOME",
        examples=["CPF"],
    )
    filtro_social: bool = Field(
        default=False,
        description="Filtrar apenas beneficiários de programas sociais",
    )
