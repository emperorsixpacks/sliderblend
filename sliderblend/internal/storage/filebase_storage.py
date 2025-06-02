import boto3
from boto3.resources.factory import ServiceResource

from sliderblend.pkg import FilebaseSettings
from sliderblend.pkg.logger import get_logger

logger = get_logger(__name__)


def _create_client(credentials: FilebaseSettings) -> ServiceResource:
    logger.debug("Creating filebase client...")
    client = boto3.client(
        "s3",
        endpoint_url="https://s3.filebase.com",
        aws_access_key_id=credentials.filebase_access_key,
        aws_secret_access_key=credentials.filebase_secret_access_key,
    )
    logger.info("Filebase client created successfully.")
    return client


class FilebaseStorage:
    def __init__(self, settings: FilebaseSettings) -> None:
        logger.debug("Initializing IBMStorage class...")
        self._client = _create_client(settings)
