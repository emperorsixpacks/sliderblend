# TODO we need to fix this so that we do not load agent settigns here
# load files in a named temp fle for processing
from uuid import UUID

from fastapi import (BackgroundTasks, Depends, FastAPI, Request, UploadFile,
                     status)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from starlette.middleware import Middleware

from sliderblend.internal import init_clients
from sliderblend.internal.entities import create_document
from sliderblend.internal.schemas import CreateDocumentSchema, UserCache
from sliderblend.internal.services import start_process
from sliderblend.pkg import (TelegramSettings, WebAppSettings, get_logger,
                             get_session)
from sliderblend.pkg.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from sliderblend.pkg.types import PROCESS_STATE, Error, Job
from sliderblend.pkg.utils import PageContext, get_templates
from sliderblend.web.dependencies import get_current_user
from sliderblend.web.middlewares import RequestLoggerMiddleware
from sliderblend.web.routers import AuthRouter, GenRouter

telegram_settings = TelegramSettings()
app_settings = WebAppSettings()
logger = get_logger()
clients = init_clients()

MIDDLEWARES = [Middleware(RequestLoggerMiddleware)]
html_templates = get_templates(app_settings)

app = FastAPI(middleware=MIDDLEWARES)
app.mount("/static", StaticFiles(directory=app_settings.STATIC_DIR), name="static")

auth_router = AuthRouter(
    telegram_settings=telegram_settings,
    redis_client=clients.REDIS_CLIENT,
)
gen_router = GenRouter(
    web_app_settings=app_settings, templates=html_templates, total_pages=4
)


def get_user_session():
    return get_current_user(redis_client=clients.REDIS_CLIENT)


@app.get("/")
async def home(request: Request) -> HTMLResponse:
    context = PageContext(
        next_step=request.url_for("upload_document"),
        request=request,
        active_page=1,
    ).dict()
    return html_templates.TemplateResponse("home.html", context)


@app.post("/create-process/")
async def create_process(
    document: UploadFile,
    background_tasks: BackgroundTasks,
    user: UserCache = Depends(get_user_session),
    session: Session = Depends(get_session),
):
    """Creates a new process, runs it in the background, and returns the
    process ID."""
    logger.info("Document received")
    # TODO get the user so we can store in the db
    job = Job()
    job, err = await clients.REDIS_JOB_CLIENT.create_job(job)
    if err:
        logger.info("Could not create job erroor: %s", err.message)
        return JSONResponse(err.message, status_code=status.HTTP_403_FORBIDDEN)

    file_contents = await document.read()
    logger.info("Checking document type")
    if not any(document.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        err = Error("Unsupported file type")
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)

    logger.info("Checking document size")
    if len(file_contents) > MAX_FILE_SIZE:
        err = Error("File too large")
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)

    logger.info("Uploading document to store")
    document_name = f"{user.telegram_username}/{document.filename}"
    file_key, err = clients.IBM_CLIENT.upload_bytes(
        data=file_contents, object_name=document_name
    )
    if err:
        logger.error("Error uploading %s to bucket, ERROR: %s", job.job_id, err.message)
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)

    doc_schema = CreateDocumentSchema(user_id=user.user_id, document_name=file_key)
    document, err = create_document(doc_schema, session)
    if err:
        job.process_state = PROCESS_STATE.FAILED
        _ = await clients.REDIS_JOB_CLIENT.update_job(job)
        logger.error(
            "Error creating document for %s, error: %s", job.job_id, err.message
        )
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)
    logger.info("Uploaded %s to bucket", job.job_id)
    job.set_file_key(file_key)
    err = await clients.REDIS_JOB_CLIENT.update_job(job)
    if err:
        logger.error("Error updating job %s ERROR: %s", job.job_id, err.message)
        return JSONResponse(err.message, status_code=status.HTTP_406_NOT_ACCEPTABLE)

    background_tasks.add_task(start_process, clients, job.job_id)
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
app.include_router(gen_router.get_router())

# TODO add telegram middleware
