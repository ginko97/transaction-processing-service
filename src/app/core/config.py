from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Production-ready settings with Pydantic v2."""

    APP_NAME: str = "Transaction Processing Service"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    VERSION: str = "0.1.0"

    # Later: DB, Kafka, etc.
    POSTGRES_URL: str = "postgresql+psycopg://user:pass@localhost:5432/transactions"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()