import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

CURRENT_FILE_DIR = Path(__file__).resolve().parent
BASE_PATH = CURRENT_FILE_DIR.parent.parent


class AppSettings(BaseSettings):
    OLLAMA_MODEL: str

    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = AppSettings()

print(settings.OLLAMA_MODEL)
