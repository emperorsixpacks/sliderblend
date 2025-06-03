from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Literal

from cohere import AsyncClientV2
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sliderblend.internal import RedisJob, get_storage_provider
from sliderblend.internal.models import DocumentEmbeddingsModel, DocumentsModel
from sliderblend.internal.services.embedding import LoadPDF, embed_document
from sliderblend.pkg import (
    BATCH_SIZE,
    CohereSettings,
    RedisSettings,
    get_logger,
    get_session,
)
from sliderblend.pkg.types import PROCESS_STATE, StorageProvider

if TYPE_CHECKING:
    from sliderblend.internal import RedisJob
    from sliderblend.pkg.types import Job, error

logger = get_logger(__name__)

RECURSIVESPLITTER = RecursiveCharacterTextSplitter(
    ["\n\n", "\n", "."], chunk_size=1500, chunk_overlap=500
)

cohere_settings = CohereSettings()
cohere_client = AsyncClientV2(cohere_settings.cohere_api_key)
redis_settings = RedisSettings()
redis_job = RedisJob(redis_settings)
session = get_session()


# TODO get file type
async def embed(storage_provider: StorageProvider, job: Job) -> error:
    logger.info("Started processing job %s", job.job_id)
    job.process_state = PROCESS_STATE.EMBEDDING
    redis_job.update_job(job)
    buffer = BytesIO()
    document = storage_provider.download_objects(job.file_key, buffer)
    chunks = RECURSIVESPLITTER.split(LoadPDF(document))

    embeddings = embed_document(cohere_client, document=chunks, batch_size=BATCH_SIZE)
    job.process_state = PROCESS_STATE.COMPLETED
    redis_job.update_job(job)
    logger.info("Done processing job %s", job.job_id)


async def start_chunkning_process(obj_store: Literal["filebase", "ibm"], job: Job):
    logger.info("Received job %s", job.job_id)
    storage_provider = get_storage_provider(obj_store)

    await embed(storage_provider, job)
    return
