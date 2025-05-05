from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import EmailStr, Field, field_validator
from sqlalchemy.orm import Mapped
from sqlmodel import Relationship, Session

from sliderblend.internal.models.base import BaseModel
from sliderblend.pkg.types import Error, error


class UserModel(BaseModel, table=True):
    __tablename__ = "users"

    telegram_username: str = Field(unique=True)
    telegram_user_id: str = Field(unique=True)
    first_name: str
    last_name: Optional[str] = Field(nullable=True)
    language_code: Optional[str] = Field(nullable=True)

    is_active: bool = Field(default=True)

    last_interaction: Optional[datetime] = Field(nullable=True)
    chat_id: int = Field(nullable=True)  # Supposed to be in message

    email: Optional[EmailStr] = Field(nullable=True)
    phone_number: Optional[str] = Field(nullable=True)
    timezone: Optional[str] = Field(
        nullable=True,
    )

    #   command_count: int = Field(default=0)
    is_blocked: bool = Field(default=False)

    @field_validator("telegram_user_id", mode="before")
    @classmethod
    def validate_telegram_id(cls, value):
        return str(value)

    def update_last_interaction(self):
        self.last_interaction = datetime.now()

    def create_user(self, session: Session) -> error:
        if not self.exists(
            field="telegram_user_id", value=self.telegram_user_id, session=session
        ):
            return Error("User exists")
        _, err = self.create(session)
        if err:
            return err
        return None
