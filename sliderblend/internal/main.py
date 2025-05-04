from cohere import AsyncClientV2

from sliderblend.internal.redis import RedisJob, RedisClient
from sliderblend.internal.ibm_storage import IBMStorage
from sliderblend.pkg import (
    AgentSettings,
    CohereSettings,
    IBMSettings,
    RedisSettings,
    get_logger,
)

logger = get_logger("init-clients")


def init_clients() -> AgentSettings:
    logger.info("Setting up client settigns")

    ibm_settings = IBMSettings()
    logger.debug(f"IBMSettings loaded: {ibm_settings}")

    redis_settings = RedisSettings()
    logger.debug(f"RedisSettings loaded: {redis_settings}")

    cohere_settings = CohereSettings()
    logger.debug(f"CohereSettings loaded: {cohere_settings}")

    ibm_storage_repo = IBMStorage(ibm_settings)
    logger.info("IBM Storage client initialized.")

    redis_client = RedisClient(redis_settings)
    logger.info("Redis client initialized.")

    redis_job = RedisJob(redis_client)
    logger.info("Redis job client initialized.")

    cohere_client = AsyncClientV2(cohere_settings.cohere_api_key)
    logger.info("Cohere client initialized.")

    logger.info("Database session created.")

    agent_settings = AgentSettings(
        REDIS_JOB_CLIENT=redis_job,
        REDIS_CLIENT=redis_client,
        COHERE_CLIENT=cohere_client,
        IBM_CLIENT=ibm_storage_repo,
    )

    logger.info("Agent settings assembled and returned.")
    return agent_settings
