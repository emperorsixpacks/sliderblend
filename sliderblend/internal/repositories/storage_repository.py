from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO, Optional, Union

import ibm_boto3
from ibm_botocore.client import Config

if TYPE_CHECKING:
    from ibm_boto3.resources.factory.s3 import ServiceResource

    from sliderblend.pkg import IBMSettings

IBM_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"


def _create_client(credentials: IBMSettings) -> ServiceResource:
    client = ibm_boto3.resource(
        service_name="s3",
        ibm_api_key_id=credentials.ibm_api_key,
        ibm_auth_endpoint=IBM_AUTH_ENDPOINT,
        ibm_service_instance_id=credentials.ibm_service_instance_id,
        config=Config(signature_version="oauth"),
        endpoint_url=credentials.ibm_service_endpoint,
    )
    return client


class IBMStorageRepository:
    def __init__(self, settings: IBMSettings) -> None:
        self.credentials = settings
        self._client = _create_client(self.credentials)

    def upload_to_bucket(
        self,
        file_data: Union[str, bytes, BinaryIO],
        object_name: str,
        folder_path: Optional[str] = None,
    ) -> str:
        """
        Upload a file to an IBM Cloud Object Storage bucket.

        Args:
            file_data: The file to upload. Can be:
                - A string path to a local file
                - Bytes content
                - A file-like object
            object_name: The name to use for the file in the bucket
            folder_path: Optional "folder" path within the bucket

        Returns:
            str: The full object key (path) where the file was stored

        Raises:
            Exception: If the upload fails
        """
        bucket_name = self.credentials.bucket_name

        # Handle virtual "folders" by prefixing the object name
        if folder_path:
            # Ensure folder path has trailing slash but no leading slash
            folder_path = folder_path.strip("/")
            if folder_path and not folder_path.endswith("/"):
                folder_path += "/"

            full_object_name = f"{folder_path}{object_name}"
        else:
            full_object_name = object_name

        try:
            # Handle different input types
            if isinstance(file_data, str):
                # It's a file path
                self._client.Object(bucket_name, full_object_name).upload_file(
                    file_data
                )
            elif isinstance(file_data, bytes):
                # It's bytes content
                file_obj = BytesIO(file_data)
                self._client.Object(bucket_name, full_object_name).upload_fileobj(
                    file_obj
                )
            else:
                # Assume it's a file-like object
                self._client.Object(bucket_name, full_object_name).upload_fileobj(
                    file_data
                )

            return full_object_name
        except Exception as e:
            raise Exception(f"Error uploading file to IBM COS: {str(e)}")

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        folder_path: Optional[str] = None,
    ) -> str:
        """
        Upload a file from disk to an IBM Cloud Object Storage bucket.

        Args:
            file_path: Path to the local file
            object_name: Optional name to use for the file in the bucket (defaults to filename)
            folder_path: Optional "folder" path within the bucket

        Returns:
            str: The full object key (path) where the file was stored
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        return self.upload_to_bucket(file_path, object_name, folder_path)

    def upload_bytes(
        self, data: bytes, object_name: str, folder_path: Optional[str] = None
    ) -> str:
        """
        Upload bytes data to an IBM Cloud Object Storage bucket.

        Args:
            data: Bytes content to upload
            object_name: Name to use for the file in the bucket
            folder_path: Optional "folder" path within the bucket

        Returns:
            str: The full object key (path) where the file was stored
        """
        return self.upload_to_bucket(data, object_name, folder_path)

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for an object.

        Args:
            key: The object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method the URL will support (default: GET)

        Returns:
            str: Presigned URL for accessing the object

        Raises:
            Exception: If URL generation fails
        """

        try:
            url = self._client.meta.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.credentials.bucket_name, "Key": key},
                ExpiresIn=expiration,
                HttpMethod=http_method,
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
