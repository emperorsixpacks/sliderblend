from typing import Optional
from uuid import UUID

from pydantic import Field

from sliderblend.internal.schemas.base import BaseSchema

class SessionData(BaseSchema):
    key: str

    def return_key(self) -> str:
        return f"user:{self.key}"


class UserCache(BaseSchema):
    id: UUID
    telegram_username: str | None = Field(default=None)
    telegram_user_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    is_active: bool
