from enum import Enum
from typing import BinaryIO, Optional, Protocol, Tuple, Union


class Error(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(message)


class FileUnit(Enum):
    KiloBytes = 0
    MegaBytes = 1


type error = Error | None


class StorageProvider(Protocol):
    def upload_to_bucket(
        self,
        file_data: Union[str, bytes, BinaryIO],
        object_name: str,
        folder_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Error]: ...

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        folder_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Error]: ...

    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        folder_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Error]: ...

    def download_bytes(
        self,
        object_name: str,
        destination: Union[str, BinaryIO],
    ) -> Tuple[Optional[bytes], Error]: ...

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> Tuple[Optional[str], Error]: ...
