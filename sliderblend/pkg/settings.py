import os
from pathlib import Path
from typing import Optional

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from sliderblend.pkg.utils import return_base_dir

env_dir = os.path.join(return_base_dir(), ".env")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_dir, env_file_encoding="utf-8", extra="ignore"
    )


class WebAppSettings(AppSettings):
    PROJECT_NAME: str = "Slide Generator API"
    BASE_DIR: Path = return_base_dir()
    TEMPLATES_DIR: Path = os.path.join(BASE_DIR, "pages")
    STATIC_DIR: Path = os.path.join(BASE_DIR, "public")


class DatabaseSettings(AppSettings):
    database_host: str
    database_port: str
    database_password: str
    database_username: str
    database_name: str

    def return_connction_string(self) -> str:
        return f"postgresql+psycopg2://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


class LLMSettings(AppSettings):
    llm_name: str
    llm_api_key: Optional[str] = None


class CohereSettings(AppSettings):
    cohere_api_key: Optional[str] = None


class RedisSettings(AppSettings):
    redis_url: AnyUrl

class IBMSettings(AppSettings):
    ibm_service_enpoint: AnyUrl
    ibm_bucket_name: str
    ibm_bucket_instance_id: str
    ibm_api_key: str
