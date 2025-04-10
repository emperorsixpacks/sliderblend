from dataclasses import dataclass
from typing import Self


@dataclass
class Error:
    message: str


type error = Error
type ModelType = Self | None
