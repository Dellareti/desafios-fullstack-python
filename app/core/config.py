from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Browser
    headless: bool = True

    # Timeout máximo por consulta em milissegundos
    timeout_ms: int = 30_000

    # Logging
    log_level: str = "INFO"

    # Servidor
    port: int = 8000

    # CORS
    cors_origins: str = "*"

    # Concorrência
    max_browser_instances: int = 5

    # Rate limiting
    rate_limit_per_minute: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        """Retorna lista de origens CORS."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
