from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class PROCESS_STATE(StrEnum):
    NOT_STARTED = "not_started"
    FAILED = "failed"
    UPLOADING = "uploading"
    EMBEDDING = "embedding"
    COMPLETED = "completed"


@dataclass(init=False)
class RedisJob:
    job_id: UUID = field(default_factory=uuid4)
    process_state: PROCESS_STATE = field(default=PROCESS_STATE.NOT_STARTED)
    file_key: str = field(default=None)
    is_complete: bool = field(default=False)
    _date_published: datetime = field(default_factory=datetime.now)

    @property
    def date_published(self) -> str:
        return self._date_published.strftime("%Y-%m-%d %H:%M:%S")

    def dict(self) -> None:
        return self.__dict__

    def set_file_key(self, key: str) -> None:
        self.file_key = key

    def completed(self) -> None:
        self.is_complete = True


type ProcessError = dict | None
type JobProcess = RedisJob | None
