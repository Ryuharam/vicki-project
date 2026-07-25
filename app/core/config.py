from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_ENV: str = "dev"

    # github apps
    WEBHOOK_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_KEY_FILE_PATH: str

    # llm model
    PROVIDER: str
    GOOGLE_MODEL: str
    GOOGLE_API_KEY: str
    ANTHROPIC_MODEL: str
    ANTHROPIC_API_KEY: str
    OLLAMA_MODEL: str

    # embedding
    EMBED_MODEL: str

    # vectordb
    VECTOR_DB_HOST: str
    VECTOR_DB_PORT: int

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
    )


settings = AppSettings()
