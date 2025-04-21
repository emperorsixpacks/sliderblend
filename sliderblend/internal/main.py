from cohere import AsyncClientV2

from sliderblend.internal import IBMStorage, RedisClient, RedisJob
from sliderblend.pkg import (
    AgentSettings,
    CohereSettings,
    IBMSettings,
    RedisSettings,
    get_session,
)


def init_clients() -> AgentSettings:
    ibm_settings = IBMSettings()
    redis_sttings = RedisSettings()
    cohere_settings = CohereSettings()

    ibm_storage_repo = IBMStorage(ibm_settings)
    redis_client = RedisClient(redis_sttings)
    redis_job = RedisJob(redis_client)

    cohere_client = AsyncClientV2(cohere_settings.cohere_api_key)

    agent_settings = AgentSettings(
        REDIS_JOB_CLIENT=redis_job,
        REDIS_CLIENT=redis_client,
        COHERE_CLIENT=cohere_client,
        DB_SESSION=get_session(),
        IBM_CLIENT=ibm_storage_repo,
    )
    return agent_settings

# diff between init_settings() -> T and init_settings() -> Type(T)
