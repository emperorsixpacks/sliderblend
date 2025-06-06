from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO, Optional, Tuple, Union

import ibm_boto3
from ibm_botocore.client import ClientError, Config

from sliderblend.pkg import get_logger
from sliderblend.pkg.types import Error, error

logger = get_logger(__name__)

if TYPE_CHECKING:
    from ibm_boto3.resources.factory.s3 import ServiceResource

    from sliderblend.pkg import IBMSettings


def _create_client(credentials: IBMSettings) -> ServiceResource:
    logger.debug("Creating IBM COS client...")
    client = ibm_boto3.client("s3",
        ibm_api_key_id=credentials.ibm_api_key,
        ibm_service_instance_id=credentials.ibm_bucket_instance_id,
        config=Config(signature_version="oauth"),
        endpoint_url=credentials.ibm_service_endpoint,
    )
    logger.info("IBM COS client created successfully.")
    return client


class IBMStorage:
    def __init__(self, settings: IBMSettings) -> None:
        logger.debug("Initializing IBMStorage class...")
        self.credentials = settings
        self._client = _create_client(self.credentials)

    def get_buckets(self):
        print("Retrieving list of buckets")
        try:
            buckets = self._client.list_buckets()
            for bucket, loc in buckets["Buckets"]:
                print("Bucket Name: {0}".format(bucket["Name"]))
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
        bucket_name = self.credentials.ibm_bucket_name
        print(self._client.list_objects(Bucket=bucket_name))
        if folder_path:
            folder_path = folder_path.strip("/")
            if folder_path and not folder_path.endswith("/"):
                folder_path += "/"
            full_object_name = f"{folder_path}{object_name}"
        else:
            full_object_name = object_name

        logger.info(f"Uploading to IBM bucket: {bucket_name}/{full_object_name}")

        try:
            if isinstance(file_data, str):
                self._client.Object(bucket_name, full_object_name).upload_file(
                    file_data
                )
            else:
                file_obj = BytesIO(file_data)
                self._client.upload_fileobj(file_obj, bucket_name, full_object_name)

            logger.info(f"Upload successful: {full_object_name}")
            return full_object_name, None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None, Error(f"Error uploading file to IBM COS: {e}")

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        folder_path: Optional[str] = None,
    ) -> Tuple[Optional[str], Error]:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None, Error(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        return self.upload_to_bucket(file_path, object_name, folder_path)

    def upload_bytes(
        self, data: bytes, object_name: str, folder_path: Optional[str] = None
    ) -> Tuple[Optional[str], Error]:
        return self.upload_to_bucket(data, object_name, folder_path)

    def downloa_bytes(
        self,
        object_name: str,
        destination: Union[str, BinaryIO] = None,
    ) -> Tuple[Optional[str], Error]:
        logger.info(f"Downloading object: {object_name}")
        try:
            self._client.download_fileobj(
                Bucket=self.credentials.ibm_bucket_name,
                Key=object_name,
                Fileobj=destination,
            )
            logger.info(f"Downloaded object: {object_name}")
            return f"<in-memory:{object_name}>", None
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None, Error(f"Error downloading object: {str(e)}")

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> Tuple[Optional[str], Error]:
        logger.info(f"Generating presigned URL for: {key}")
        try:
            url = self._client.meta.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.credentials.bucket_name, "Key": key},
                ExpiresIn=expiration,
                HttpMethod=http_method,
            )
            logger.debug(f"Presigned URL generated: {url}")
            return url, None
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return None, error(f"Failed to generate presigned URL: {str(e)}")
