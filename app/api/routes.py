import logging

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.models.request import ConsultaRequest
from app.models.response import ConsultaResponse
from app.services.consulta_service import ConsultaService

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1")


@router.get(
    "/health",
    summary="Health check",
    tags=["Infra"],
    response_model=dict[str, str],
)
async def health_check() -> dict[str, str]:
    """Verifica se a API está operacional."""
    return {"status": "ok", "version": "0.1.0"}


@router.post(
    "/consulta",
    summary="Consultar pessoa física no Portal da Transparência",
    tags=["Consulta"],
    response_model=ConsultaResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def consultar_pessoa(
    request: Request,
    body: ConsultaRequest,
) -> ConsultaResponse:
    """
    Executa consulta de pessoa física no Portal da Transparência.

    Aceita CPF, NIS ou Nome como identificador.
    Retorna dados básicos, benefícios sociais e screenshot da página.
    """
    service = ConsultaService()
    resultado = await service.executar(body)
    return resultado
