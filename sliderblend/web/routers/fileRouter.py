from fastapi import APIRouter, File, HTTPException, UploadFile, status

from sliderblend.internal import IBMStorage
from sliderblend.internal.exceptions import IBMStorageError
from sliderblend.pkg.settings import IBMSettings
from sliderblend.web.exception import StorageHTTPException

ibm_settings = IBMSettings()
ibm_storage_repo = IBMStorage(ibm_settings)

file_router = APIRouter(prefix="/file")


MAX_FILE_SIZE = 15 * 1024 * 1024  # MB in bytes
ALLOWED_EXTENSIONS = {".pdf"}


async def upload_file_to_s3(file: UploadFile = File(...)):
    try:
        # Validate file extension
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF files are allowed.",
            )

        # Read file contents
        file_contents = await file.read()
        # Validate file size
        if len(file_contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the 15MB limit.",
            )

        # Upload to IBM COS
        file_key = ibm_storage_repo.upload_bytes(
            data=file_contents, object_name=file.filename
        )

        return {"message": "File uploaded successfully", "file_key": file_key}

    except (HTTPException, IBMStorageError) as e:
        raise StorageHTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e
