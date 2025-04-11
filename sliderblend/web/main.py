from uuid import UUID

from fastapi import BackgroundTasks, FastAPI, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from sliderblend.internal import IBMStorage, IBMStorageError, RedisClient
from sliderblend.pkg import (
    IBMSettings,
    RedisSettings,
    TelegramSettings,
    WebAppSettings,
    get_logger,
)
from sliderblend.pkg.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from sliderblend.pkg.types import RedisJob
from sliderblend.pkg.types.redis_types import PROCESS_STATE
from sliderblend.pkg.utils import get_templates
from sliderblend.web.routers import AuthRouter, GenRouter

logger = get_logger()
telegram_settings = TelegramSettings()
ibm_settings = IBMSettings()
redis_sttings = RedisSettings()
app_settings = WebAppSettings()
ibm_storage_repo = IBMStorage(ibm_settings)
redis_client = RedisClient(redis_sttings)
html_templates = get_templates(app_settings)

app = FastAPI()
app.mount("/static", StaticFiles(directory=app_settings.STATIC_DIR), name="static")

auth_router = AuthRouter(telegram_settings=telegram_settings)
gen_router = GenRouter(web_app_settings=app_settings, templates=html_templates, total_pages=4)


@app.get("/")
async def home(request: Request):
    upload_url = request.url_for("get_started")
    return RedirectResponse(upload_url)


@app.get("/create-process/")
async def create_process(file: UploadFile, background_tasks: BackgroundTasks):
    """Creates a new process, runs it in the background, and returns the
    process ID."""
    # TODO get the user so we can store in the db
    job = RedisJob()
    file_contents = await file.read()
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        error = {"error": "Invalid file type"}
        logger.info(
            "Error uploading %s to bucket, ERROR: %s", job.job_id, error["error"]
        )
        return JSONResponse(
            "Unsupported file type", status_code=status.HTTP_406_NOT_ACCEPTABLE
        )

    if len(file_contents) > MAX_FILE_SIZE:
        error = {"error": "File too large"}
        logger.info(
            "Error uploading %s to bucket, ERROR: %s", job.job_id, error["error"]
        )
        return JSONResponse(
            "File Too large", status_code=status.HTTP_406_NOT_ACCEPTABLE
        )
    try:
        file_key = ibm_storage_repo.upload_bytes(
            data=file_contents, object_name=file.filename
        )
        logger.info("Uploaded %s to bucket", job.job_id)

    except IBMStorageError:
        error = {"error": "File too large"}
        logger.info(
            "Error uploading %s to bucket, ERROR: %s", job.job_id, error["error"]
        )
        return job, error

    job.process_state = PROCESS_STATE.UPLOADING
    job.set_file_key(file_key)
    redis_client.new_job(job)
    #    background_tasks.add_task(background_job, job_id)

    return {"process_id": str(job.job_id)}  # Return process ID


@app.get("/process/{process_id:str}")
def get_process_status(process_id: UUID):
    pass


app.include_router(gen_router.get_router())
app.include_router(auth_router.get_router())
