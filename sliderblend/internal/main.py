from cohere import AsyncClientV2

from sliderblend.internal.storage import get_storage_provider 
from sliderblend.internal.redis import RedisClient, RedisJob
from sliderblend.pkg import (ClientSettings, CohereSettings, FilebaseSettings,
                             RedisSettings, get_logger)

logger = get_logger(__name__)


async def init_clients() -> ClientSettings:
    logger.info("Setting up client settings")

    # Load settings
    storage_settings = FilebaseSettings()
    redis_settings = RedisSettings()
    cohere_settings = CohereSettings()

    # Initialize clients
    ibm_storage_repo = get_storage_provider("filebase", storage_settings)
    redis_client = RedisClient(redis_settings)
    redis_job = RedisJob(redis_settings)
    cohere_client = AsyncClientV2(cohere_settings.cohere_api_key)

    logger.info("All clients initialized")

    return ClientSettings(
        REDIS_JOB=redis_job,
        REDIS_CLIENT=redis_client,
        COHERE_CLIENT=cohere_client,
        IBM_CLIENT=ibm_storage_repo,
    )
