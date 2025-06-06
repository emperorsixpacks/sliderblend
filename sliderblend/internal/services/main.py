from __future__ import annotations

import re
from io import BytesIO
from typing import TYPE_CHECKING, Literal

from cohere import AsyncClientV2
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sliderblend.internal import RedisJob, get_storage_provider
from sliderblend.internal.entities import create_document_embedding
from sliderblend.internal.schemas import CreateDocumentEmbeddingSchema
from sliderblend.internal.services.embedding import LoadPDF, embed_document
from sliderblend.pkg import (
    BATCH_SIZE,
    CohereSettings,
    FilebaseSettings,
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
    ["\n\n", "\n", "."], chunk_size=500, chunk_overlap=50
)

cohere_settings = CohereSettings()
redis_settings = RedisSettings()
filebase_settings = FilebaseSettings()

redis_job = RedisJob(redis_settings)
cohere_client = AsyncClientV2(cohere_settings.cohere_api_key)
session = get_session()


# TODO get file type
async def embed(storage_provider: StorageProvider, job: Job) -> error:
    try:
        logger.info("job %s: Processing ", job.job_id)
        job.process_state = PROCESS_STATE.EMBEDDING
        metadata = job.metadata
        document_id = metadata["document_id"]
        docuemnt_key = metadata["file_key"]
        docuemnt_key = f"documents/{docuemnt_key}"
        file_name = re.sub(r"^.*[/:]", "", docuemnt_key)
        buffer = BytesIO()

        await redis_job.update_job(job)
        logger.info("job %s: Downloading document bytes", job.job_id)
        _, err = storage_provider.download_bytes(docuemnt_key, buffer)  # bytes
        if err:
            job.process_state = PROCESS_STATE.FAILED
            _ = await redis_job.update_job(job)
            logger.error(
                "job %s: Could not download document bytes, %s",
                job.job_id,
                err.message,
            )
            return
        logger.info("job %s: Embedding document", job.job_id)

        loader = LoadPDF(name=file_name, source=buffer)
        load_documents, err = loader.load()
        if err:
            logger.error(err.message)
            return
        chunked_document = RECURSIVESPLITTER.split_documents(load_documents)

        embeddings = await embed_document(
            cohere_client,
            document=[chunk.page_content for chunk in chunked_document],
            batch_size=BATCH_SIZE,
        )
        document_embedding = CreateDocumentEmbeddingSchema(
            document=chunked_document, embedding=embeddings, document_id=document_id
        )
        logger.info("job %s: Saving embeddings", job.job_id)
        err = create_document_embedding(schema=document_embedding, db=session)
        if err:
            job.process_state = PROCESS_STATE.FAILED
            _ = await redis_job.update_job(job)
            logger.error(
                "job %s: %s",
                job.job_id,
                err.message,
            )
            return
        job.process_state = PROCESS_STATE.COMPLETED
        await redis_job.update_job(job)
        logger.info("job %s: Done", job.job_id)
        session.commit()
    except Exception as e:
        logger.error(e, stack_info=True)


async def start_chunkning_process(obj_store: Literal["filebase", "ibm"], job: Job):
    logger.info("Received job %s", job.job_id)
    storage_provider, err = get_storage_provider(obj_store, filebase_settings)
    if err:
        logger.error(err.message)
        return

    logger.info("Starting job %s", job.job_id)
    await embed(storage_provider, job)
    return
