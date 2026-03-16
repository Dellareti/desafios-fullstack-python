import logging
from types import TracebackType
from typing import Self

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class BrowserManager:
    """
    Context manager assíncrono que gerencia o ciclo de vida de uma instância
    do Playwright.  Cada instância é independente — sem estado global — para
    suportar execuções paralelas.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "BrowserManager":
        logger.debug("Iniciando instância do Playwright")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--single-process",
            ],
        )
        self._context = await self._browser.new_context(
            user_agent=_USER_AGENT,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            viewport={"width": 1366, "height": 768},
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(settings.timeout_ms)
        logger.debug("Browser iniciado com sucesso")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.debug("Encerrando instância do Playwright")
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        """Retorna a página ativa."""
        if self._page is None:
            raise RuntimeError("BrowserManager não foi inicializado via 'async with'")
        return self._page
