from io import BytesIO
from typing import BinaryIO, Optional, Tuple, Union

import boto3
from boto3.resources.factory import ServiceResource
from botocore.client import ClientError

from sliderblend.pkg import FilebaseSettings
from sliderblend.pkg.logger import get_logger
from sliderblend.pkg.types import Error, error

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
        self.credentials = settings
        self._client = _create_client(self.credentials)

    def get_buckets(self):
        print("Retrieving list of buckets")
        try:
            buckets = self._client.list_buckets()
            for bucket, _ in buckets["Buckets"]:
                print(f"Bucket Name: {bucket['Name']}")
        except ClientError as be:
            print("CLIENT ERROR: {0}\n".format(be))
        except Exception as e:
            print("Unable to retrieve list buckets: {0}".format(e))

    def upload_to_bucket(
        self,
        file_data: Union[str, bytes, BinaryIO],
        object_name: str,
        folder_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Error]:
        bucket_name = self.credentials.filebase_bucket_name
        if folder_path:
            folder_path = folder_path.strip("/")
            if folder_path and not folder_path.endswith("/"):
                folder_path += "/"
            full_object_name = f"{folder_path}{object_name}"
        else:
            full_object_name = object_name

        logger.info(f"Uploading to filebase bucket: {bucket_name}/{full_object_name}")

        try:
            if isinstance(file_data, str):
                self._client.Object(bucket_name, full_object_name).upload_file(
                    file_data
                )
            elif isinstance(file_data, BytesIO):
                self._client.upload_fileobj(file_data, bucket_name, full_object_name)
            elif isinstance(file_data, (bytes, bytearray)):
                file_obj = BytesIO(file_data)

                self._client.upload_fileobj(file_obj, bucket_name, full_object_name)

            logger.info(f"Upload successful: {full_object_name}")
            return full_object_name, None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None, Error(f"Error uploading file to filebase: {e}")

    def upload_bytes(
        self, data: bytes, object_name: str, folder_path: Optional[str] = None
    ) -> Tuple[Optional[str], Error]:
        return self.upload_to_bucket(data, object_name, folder_path)

    def download_bytes(
        self,
        object_name: str,
        destination: Union[str, BinaryIO] = None,
    ) -> Tuple[Optional[str], Error]:
        logger.info(f"Downloading object: {object_name}")
        try:
            self._client.download_fileobj(
                Bucket=self.credentials.filebase_bucket_name,
                Key=object_name,
                Fileobj=destination,
            )
            logger.info(f"Downloaded object: {object_name}")
            return f"<in-memory:{object_name}>", None
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None, Error(f"Error downloading object: {str(e)}")
