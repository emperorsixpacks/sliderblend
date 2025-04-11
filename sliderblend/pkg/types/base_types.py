from typing import Self


class Error(Exception):
    message: str
    field: str | None

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


type error = Error | None
type ModelType = Self | None
