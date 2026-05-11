from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Transaction Processing Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    VERSION: str = "0.1.0"
    POSTGRES_URL: str = "postgresql+psycopg://user:pass@localhost:5432/transactions"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
