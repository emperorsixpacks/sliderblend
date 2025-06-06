import hashlib
import hmac
import json
import os
import re
from enum import StrEnum

from jinja2 import pass_context
from pydantic_core.core_schema import dict_schema

from sliderblend.pkg.types import FileUnit


def return_base_dir():
    return get_dir_at_level(3)


def get_dir_at_level(level=1, file: str = __file__):
    current_path = os.path.dirname(file)
    if level < 0:
        raise ValueError("Level cannot be less than 0")
    if level == 0:
        return os.path.dirname(file)
    return get_dir_at_level(level - 1, current_path)


def exists(path: str) -> bool:
    return os.path.exists(path)


def get_file_size(data: bytes) -> float:
    """
    Returns the size of a bytes object in the specified unit.

    Args:
        data (bytes): The bytes object to measure.

    Returns:
        float: The size of the data in the specified unit.
    """
    size_in_bytes = len(data)

    return size_in_bytes


def format_file_size(size_in_bytes: int) -> FileUnit:
    """
    Returns a human-readable file size from a size in bytes.

    Args:
        size_in_bytes (int): The file size in bytes.

    Returns:
        str: The file size formatted with the appropriate unit.
    """
    if size_in_bytes < 1024:
        return FileUnit.KiloBytes
    if size_in_bytes < 1024**2:
        return FileUnit.MegaBytes


def file_size_kb(size: int):
    return size // (1024)


def sanitize_filename(filename: str) -> str:
    basename = filename.split("/")[-1].split("\\")[-1]
    no_spaces = basename.replace(" ", "_")
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "", no_spaces)
    return cleaned.lower()


def create_signature(secret_key: str, payload: dict) -> str:
    paylod_str = json.dumps(payload)
    computed_hash = hmac.new(secret_key.encode(), paylod_str.encode(), hashlib.sha256)
    return computed_hash.hexdigest()


def verifiy_payload(secret_key: str, signature: str, payload: dict) -> bool:
    computed_hash = create_signature(secret_key, payload)
    return hmac.compare_digest(signature, computed_hash)


class Prompt:
    def __init__(self, prompt_name: str, /, **kwargs: str) -> None:
        self.prompt_name = prompt_name
        self.prompt_path = os.path.join(
            return_base_dir(), f"prompts/{self.prompt_name}.txt"
        )
        self.prompt_params = kwargs

    def read(self) -> str:
        prompt: str = None
        if not exists(self.prompt_path):
            raise FileNotFoundError(f"Prompt {self.prompt_name} does not exist")
        with open(self.prompt_path, encoding="utf-8") as file:
            prompt = file.read()
            file.close()

        return prompt.format_map(self.prompt_params)

    from enum import Enum


class ValidFileType(StrEnum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    TXT = "text/plain"

    @classmethod
    def is_valid(cls, mime_type: str) -> bool:
        return mime_type in cls._value2member_map_
