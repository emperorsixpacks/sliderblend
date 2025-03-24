from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from pydantic import ConfigDict, EmailStr
from sqlmodel import Field, Relationship, SQLModel

from sliderblend.utils import KB, MB


class FileSize(Enum):
    KiloBytes = 0
    MegaBytes = 1


class BaseModel(SQLModel):
    model_config = ConfigDict(
        use_enum_values=True, validate_assignment=True, populate_by_name=True
    )
    id: UUID = Field(default_factory=lambda x: str(uuid4()), primary_key=True)
    created_date: datetime = Field(default_factory=datetime.now())


class User(BaseModel, table=True):
    __tablename__ = "users"

    telegram_username: Optional[str] = Field(
        nullable=True, comment="Telegram username (if set)"
    )
    first_name: str = Field(nullable=False, comment="User's first name from Telegram")
    last_name: Optional[str] = Field(
        nullable=True, comment="user's last name from Telegram"
    )
    language_code: Optional[str] = Field(
        nullable=True, comment="User's language code (e.g., 'en')"
    )

    is_active: bool = Field(
        default=True, comment="Whether the user is currently active"
    )

    last_interaction: Optional[datetime] = Field(
        nullable=True, comment="Last time user interacted with bot"
    )
    chat_id: int = Field(nullable=False, comment="Telegram chat ID for messaging")

    email: Optional[EmailStr] = Field(nullable=True, comment="User's email address")
    phone_number: Optional[str] = Field(nullable=True, comment="User's phone number")
    timezone: Optional[str] = Field(
        nullable=True,
        comment="User's timezone (e.g., 'UTC', 'America/New_York')",
    )

    command_count: int = Field(default=0, comment="Number of commands executed by user")
    is_blocked: bool = Field(
        default=False, comment="Whether the user is blocked from using the bot"
    )
    documents: List["Documents"] = Relationship(back_populates="user")

    def update_last_interaction(self):
        self.last_interaction = datetime.now()


class Documents(BaseModel, table=True):
    __tablename__ = "documents"
    number_of_pages: int = Field(nullable=False)
    size: int = Field(nullable=False)
    unit: FileSize = Field(nullable=False)
    is_embedded: bool = Field(default=False, nullable=False)
    user: "User" = Relationship(back_populates="documents")
    embedding: Optional["DocumentEmbeddings"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"uselist": False},  # Ensures one-to-one
    )

    def get_size_in_unit(self) -> str:
        if self.unit == FileSize.KiloBytes:
            return f"{self.size * KB}kb"
        if self.unit == FileSize.MegaBytes:
            return f"{self.size * MB}mb"


class DocumentEmbeddings(BaseModel, table=True):
    __tablename_ = "users"
    text: str
    embedding: Any = Field(sa_type=Vector(1024))
    page_number: int = Field(nullable=False)
    document: "Documents" = Relationship(back_populates="embedding")
