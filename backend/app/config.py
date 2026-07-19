from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Static/bootstrap configuration, read from .env only.

    Provider tokens and integration settings are never read from here —
    they live encrypted in the `settings` table (see GOAL.md config rules).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://gatewayhub:gatewayhub@localhost:5432/gatewayhub"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "changeme-secret-key"
    app_port: int = 8000
    admin_email: str = "admin@local"
    admin_password: str = "changeme"


@lru_cache
def get_settings() -> Settings:
    return Settings()
