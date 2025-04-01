from fastapi import APIRouter

file_router = APIRouter(prefix="/file")


@file_router.get("/upload")
def upload_file_to_s3():
    return None
