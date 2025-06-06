from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session

from sliderblend.internal.entities import create_document
from sliderblend.internal.schemas import (
    BotChunkRequestSchema,
    CreateDocumentSchema,
    UserCache,
)
from sliderblend.internal.services import start_chunkning_process
from sliderblend.pkg import get_session
from sliderblend.pkg.logger import get_logger
from sliderblend.pkg.types import FileUnit, Job
from sliderblend.server.dependencies import get_bot_req_user, get_redis_job

if TYPE_CHECKING:
    from sliderblend.internal import RedisJob

logger = get_logger(__name__)


class BotRouter:
    def get_router(self):
        router = APIRouter(prefix="/bot")
        router.add_api_route("/chunk", self.chunk_document_job, methods=["POST"])
        return router

    async def chunk_document_job(
        self,
        request: Request,
        payload: BotChunkRequestSchema,
        background_tasks: BackgroundTasks,
        user: UserCache = Depends(get_bot_req_user),
        session: Session = Depends(get_session),
        redis_job: RedisJob = Depends(get_redis_job),
    ):
        doc_schema = CreateDocumentSchema(
            user_id=user.id,
            document_name=payload.file_id,
            size=payload.size,
            number_of_pages=payload.number_of_pages,
        )
        document, err = create_document(doc_schema, session)
        if err:
            logger.error(err.message)
            return JSONResponse(
                "Could not create docuemnt",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        job = Job(metadata={"document_id":document.id, "file_key": document.document_name})
        job, err = await redis_job.create_job(job)
        if err:
            logger.error("Could not create job, error: %s", err.message)
            return JSONResponse(
                err.message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        logger.info("Created job %s", job.job_id)
        err = await redis_job.update_job(job)
        if err:
            logger.error("Error updating job %s ERROR: %s", job.job_id, err.message)
            return (
                {"error": "One minute we need bigger servers :)", "request": request},
            )

        background_tasks.add_task(start_chunkning_process, "filebase", job)
        logger.info("Created background process for: %s", job.job_id)
        session.commit()
        return {"process_id": str(job.job_id)}  # Return process ID
