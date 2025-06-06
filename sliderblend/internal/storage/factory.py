from typing import Union

from sliderblend.internal.storage.filebase_storage import FilebaseStorage
from sliderblend.internal.storage.ibm_storage import IBMStorage
from sliderblend.pkg import FilebaseSettings, IBMSettings, get_logger
from sliderblend.pkg.types import Error, StorageProvider, error

logger = get_logger(__name__)


def get_storage_provider(
    provider: str, settings: Union[IBMSettings, FilebaseSettings]
) -> tuple[StorageProvider, error]:
    provider = provider.lower()
    logger.info("Creating storage bucket for %s", provider)
    if provider == "ibm":
        logger.info("Creating IBM storage")
        return IBMStorage(settings), None
    if provider == "filebase":
        logger.info("Creating Filebase storage")
        return FilebaseStorage(settings), None
    return None, Error(f"Unsupported storage provider: {provider}")
