from typing import Union

from sliderblend.internal.storage.filebase_storage import FilebaseStorage
from sliderblend.internal.storage.ibm_storage import IBMStorage
from sliderblend.pkg import FilebaseSettings, IBMSettings
from sliderblend.pkg.types import StorageProvider


def get_storage_provider(
    provider: str, settings: Union[IBMSettings, FilebaseSettings]
) -> StorageProvider:
    provider = provider.lower()
    if provider == "ibm":
        return IBMStorage(settings)
    if provider == "filebase":
        return FilebaseStorage(settings)
    raise ValueError(f"Unsupported storage provider: {provider}")
