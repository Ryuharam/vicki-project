from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode


class AppSettings(BaseSettings):
    APP_ENV: str = "dev"

    # github apps
    WEBHOOK_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_KEY_FILE_PATH: str

    # llm model
    LLM_PRIMARY: str
    LLM_FALLBACKS: Annotated[list[str], NoDecode] = []

    GOOGLE_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # embedding
    EMBED_MODEL: str

    # vectordb
    VECTOR_DB_HOST: str
    VECTOR_DB_PORT: int

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("LLM_FALLBACKS", mode="before")
    @classmethod
    def _split_comma_separated(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
