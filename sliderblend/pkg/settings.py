import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from sliderblend.utils import BASE_DIR

env_dir = os.path.join(BASE_DIR, ".env")


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_dir, env_file_encoding="utf-8", extra="ignore"
    )


class WebAppSettings(BaseAppSettings):
    PROJECT_NAME: str = "Slide Generator API"
    BASE_DIR: Path = BASE_DIR
    TEMPLATES_DIR: Path = os.path.join(BASE_DIR, "templates")
    STATIC_DIR: Path = os.path.join(BASE_DIR, "static")


class DatabaseSettings(BaseAppSettings):
    database_host: str
    database_port: str
    database_password: str
    database_username: str
    database_name: str

    def return_connction_string(self) -> str:
        return f"postgresql+psycopg2://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


class LLMSettings(BaseAppSettings):
    llm_name: str
    llm_api_key: Optional[str] = None


class CohereSettings(BaseAppSettings):
    cohere_api_key: Optional[str] = None
