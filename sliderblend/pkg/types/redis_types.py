from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Dict
from uuid import UUID, uuid4


class PROCESS_STATE(StrEnum):
    NOT_STARTED = "not_started"
    FAILED = "failed"
    UPLOADING = "uploading"
    EMBEDDING = "embedding"
    COMPLETED = "completed"


@dataclass
class Job:
    job_id: UUID = field(default_factory=uuid4, init=False)
    process_state: PROCESS_STATE = field(default=PROCESS_STATE.NOT_STARTED, init=False)
    metadata: Dict[str, any] = field(default=None)
    is_complete: bool = field(default=False, init=False)
    _date_published: datetime = field(default_factory=datetime.now, init=False)

    @property
    def date_published(self) -> str:
        return self._date_published.strftime("%Y-%m-%d %H:%M:%S")

    def dict(self) -> None:
        return self.__dict__

    def completed(self) -> None:
        self.is_complete = True
