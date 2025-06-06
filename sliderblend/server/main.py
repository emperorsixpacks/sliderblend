from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlmodel import Session
from starlette.middleware import Middleware

from sliderblend.internal import init_clients
from sliderblend.internal.entities import create_document
from sliderblend.internal.schemas import CreateDocumentSchema, UserCache
from sliderblend.internal.services import start_chunkning_process
from sliderblend.pkg import (
    ClientSettings,
    TelegramSettings,
    WebAppSettings,
    get_logger,
    get_session,
)
from sliderblend.pkg.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from sliderblend.pkg.types import PROCESS_STATE, Error, Job
from sliderblend.pkg.utils import PageContext, get_templates
from sliderblend.server.dependencies import (
    get_client_session,
    get_clients,
    get_current_user,
)
from sliderblend.server.middlewares import RequestLoggerMiddleware
from sliderblend.server.routers import AuthRouter, BotRouter, UserRouter

telegram_settings = TelegramSettings()
app_settings = WebAppSettings()

logger = get_logger(__name__)

MIDDLEWARES = [Middleware(CORSMiddleware), Middleware(RequestLoggerMiddleware)]
html_templates = get_templates(app_settings)


auth_router = AuthRouter(
    telegram_settings=telegram_settings,
)
user_router = UserRouter()
bot_router = BotRouter()


@asynccontextmanager
async def lifespan(a: FastAPI):
    # Initialize all clients at startup
    clients = await init_clients()
    a.state.clients = clients
    logger.info("Service initialization complete")

    yield  # App runs here

    # Cleanup resources at shutdown
    # await clients.REDIS_CLIENT.close()
    # await clients.COHERE_CLIENT.close()
    # logger.info("Services shut down gracefully")


app = FastAPI(
    lifespan=lifespan,
    middleware=MIDDLEWARES,
)


@app.get("/")
async def home(request: Request) -> HTMLResponse:
    context = PageContext(
        next_step=request.url_for("upload_document"),
        request=request,
        active_page=1,
    ).dict()
    return html_templates.TemplateResponse("home.html", context)


@app.post("/create-process")
async def create_process(
    request: Request,
    document: UploadFile,
    background_tasks: BackgroundTasks,
    user: UserCache = Depends(get_current_user),
    session: Session = Depends(get_session),
    clients: ClientSettings = Depends(get_clients),
):
    """Creates a new process, runs it in the background, and returns the
    process ID."""
    logger.info("Document received")
    # TODO get the user so we can store in the db
    file_contents = await document.read()
    logger.info("Checking document type")
    if not any(document.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        err = Error("Unsupported file type")
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return html_templates.TemplateResponse(
            "partials/upload_error.html",
            {"error": err.message, "request": request},
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
    logger.info("Checking document size")
    if document.size > MAX_FILE_SIZE:
        err = Error("File too large (max 15MB)")
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return html_templates.TemplateResponse(
            "partials/upload_error.html",
            {"error": err.message, "request": request},
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
        )
    logger.info("Uploading document to store")
    document_name = f"{user.telegram_username}/{document.filename}"
    file_key, err = clients.IBM_CLIENT.upload_bytes(
        data=file_contents, object_name=document_name
    )
    if err:
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return html_templates.TemplateResponse(
            "partials/upload_error.html",
            {"error": "One minute we need bigger servers :)", "request": request},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    doc_schema = CreateDocumentSchema(user_id=user.user_id, document_name=file_key)
    document, err = create_document(doc_schema, session)
    if err:
        job.process_state = PROCESS_STATE.FAILED
        _ = await clients.REDIS_JOB.update_job(job)
        logger.error(
            "Error creating document for %s, error: %s", job.job_id, err.message
        )
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)
    logger.info("Uploaded %s to bucket", job.job_id)
    err = await clients.REDIS_JOB.update_job(job)
    if err:
        logger.error("Error updating job %s ERROR: %s", job.job_id, err.message)
        return html_templates.TemplateResponse(
            "partials/upload_error.html",
            {"error": "One minute we need bigger servers :)", "request": request},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    background_tasks.add_task(start_chunkning_process, clients, job.job_id)
    logger.info("Created background process for: %s", job.job_id)

    logger.info("Success uploading %s to bucket", job.job_id)
    return {"process_id": str(job.job_id)}  # Return process ID


@app.get("/error")
def error_page(message: str, request: Request):
    context = {"message": message, "request": request}
    return html_templates.TemplateResponse("error.html", context)


@app.get("/process/{process_id:str}")
def get_process_status(process_id: UUID):
    pass


app.include_router(auth_router.get_router())
app.include_router(user_router.get_router())
app.include_router(bot_router.get_router())

# TODO add telegram middleware
# TODO why cores, seems like I have forgotten again
# TODO add htmx only reqest headers this could affect callback since this is not an htmx request
# TODO add allow headers middleware
