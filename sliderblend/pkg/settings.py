from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from cohere.client_v2 import AsyncClientV2, ClientV2
from pydantic_settings import BaseSettings, SettingsConfigDict

from sliderblend.pkg.utils import return_base_dir

if TYPE_CHECKING:
    from sliderblend.internal import IBMStorage
    from sliderblend.internal.redis import RedisClient, RedisJob


env_dir = os.path.join(return_base_dir(), ".env")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_dir, env_file_encoding="utf-8", extra="ignore"
    )


class WebAppSettings(AppSettings):
    PROJECT_NAME: str = "Slide Generator API"
    BASE_DIR: Path = return_base_dir()
    TEMPLATES_DIR: Path = os.path.join(BASE_DIR, "pages")


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
    redis_port: int
    redis_host: str
    redis_username: str = ""
    redis_password: str


class IBMSettings(AppSettings):
    ibm_service_endpoint: str
    ibm_bucket_name: str
    ibm_bucket_instance_id: str
    ibm_api_key: str


class FilebaseSettings(AppSettings):
    filebase_bucket_name: str
    filebase_access_key: str
    filebase_secret_access_key: str


class TelegramSettings(AppSettings):
    telegram_bot_token: str


class AppSecret(AppSettings):
    app_secret: str


@dataclass
class ClientSettings:
    REDIS_CLIENT: Optional[RedisClient] = None
    REDIS_JOB: Optional[RedisJob] = None
    COHERE_CLIENT: Optional[Union[AsyncClientV2, ClientV2]] = None
    IBM_CLIENT: Optional[IBMStorage] = None
