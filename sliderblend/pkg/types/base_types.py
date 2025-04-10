from dataclasses import dataclass


@dataclass
class Error:
    message: str


type error = Error
