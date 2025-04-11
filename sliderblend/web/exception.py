from fastapi import HTTPException, status


class StorageHTTPException(HTTPException):
    """Custom HTTP Exception for IBM Storage errors."""

    def __init__(
        self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(status_code=status_code, detail=detail)
