from uuid import UUID

from fastapi import (BackgroundTasks, Depends, FastAPI, Request, UploadFile,
                     status)
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from sliderblend.internal import (DocumentsModel, IBMStorage, IBMStorageError,
                                  RedisClient, UserModel)
from sliderblend.pkg import (IBMSettings, RedisSettings, TelegramSettings,
                             WebAppSettings, get_logger, get_session)
from sliderblend.pkg.constants import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from sliderblend.pkg.types import RedisJob, TelegramInitData
from sliderblend.pkg.types.redis_types import PROCESS_STATE
from sliderblend.pkg.utils import verify_tg_init_data
from sliderblend.web.dependencies import get_current_user
from sliderblend.web.routes import gen_router
logger = get_logger()
ibm_settings = IBMSettings()
redis_sttings = RedisSettings()
app_settings = WebAppSettings()
telegram_settings = TelegramSettings()
ibm_storage_repo = IBMStorage(ibm_settings)
redis_client = RedisClient(redis_sttings)

app = FastAPI()
app.mount("/static", StaticFiles(directory=app_settings.STATIC_DIR), name="static")


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


@app.post("/callback/")
def callback_url(request: Request, data: dict, session: Session = Depends(get_session)):
    init_data = TelegramInitData.from_string(data["initData"])
    data, err = verify_tg_init_data(init_data, telegram_settings.telegram_bot_token)
    if err:
        print(err.message)
        return JSONResponse(content=err.message, status_code=status.HTTP_403_FORBIDDEN)
    user_data = init_data.user
    _, err = UserModel.get(
        field="telegram_user_id", value=str(user_data.telegram_user_id), session=session
    )
    if err:
        new_user = UserModel(**user_data.model_dump())
        err = new_user.create_user(session)
        if err:
            print(err.message)
            return JSONResponse(
                content=err.message, status_code=status.HTTP_403_FORBIDDEN
            )

    return {"ok": True}


app.include_router(gen_router)
"""
if ((new Date() - new Date(params.auth_date * 1000)) > 86400000) { // milisecond
    throw new ValidationError('Authorization data is outdated');
}
"""
