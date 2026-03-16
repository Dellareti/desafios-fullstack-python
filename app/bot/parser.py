import logging
import re
from datetime import date

logger = logging.getLogger(__name__)

_VALOR_RE = re.compile(r"R\$\s*([\d.,]+)")
_DATA_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def limpar_texto(texto: str | None) -> str:
    """Remove espaços extras e caracteres de controle de uma string."""
    if not texto:
        return ""
    return " ".join(texto.split())


def parse_valor_monetario(texto: str) -> float:
    """
    Converte string monetária brasileira em float.

    Exemplos:
        "R$ 1.234,56" -> 1234.56
        "R$ 600,00"   -> 600.0
    """
    match = _VALOR_RE.search(texto)
    if not match:
        logger.warning("Não foi possível extrair valor monetário de: %r", texto)
        return 0.0
    raw = match.group(1)
    # Remove pontos de milhar e substitui vírgula decimal
    normalizado = raw.replace(".", "").replace(",", ".")
    try:
        return float(normalizado)
    except ValueError:
        logger.warning("Valor inválido após normalização: %r", normalizado)
        return 0.0


def parse_data_br_para_iso(texto: str) -> str | None:
    """
    Converte data no formato DD/MM/YYYY para ISO 8601 (YYYY-MM-DD).

    Retorna None se o texto não contiver uma data válida.
    """
    match = _DATA_RE.search(texto)
    if not match:
        return None
    dia, mes, ano = match.group(1), match.group(2), match.group(3)
    try:
        return date(int(ano), int(mes), int(dia)).isoformat()
    except ValueError:
        logger.warning("Data inválida: %s/%s/%s", dia, mes, ano)
        return None


def parse_competencia(texto: str) -> str:
    """
    Normaliza o texto de competência (ex: 'Jan/2024' -> '01/2024').
    Retorna o texto original limpo se não conseguir normalizar.
    """
    meses = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12",
    }
    texto_limpo = limpar_texto(texto).lower()
    for nome, num in meses.items():
        if nome in texto_limpo:
            ano_match = re.search(r"\d{4}", texto_limpo)
            if ano_match:
                return f"{num}/{ano_match.group()}"
    return limpar_texto(texto)
