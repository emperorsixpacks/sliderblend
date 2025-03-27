from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from pydantic import ConfigDict, EmailStr
from sqlmodel import Field, Relationship, SQLModel
from sliderblend import constants

class FileSize(Enum):
    KiloBytes = 0
    MegaBytes = 1


class BaseModel(SQLModel):
    model_config = ConfigDict(
        use_enum_values=True, validate_assignment=True, populate_by_name=True
    )
    id: UUID = Field(default_factory=lambda x: str(uuid4()), primary_key=True)
    created_date: datetime = Field(default_factory=datetime.now)


class User(BaseModel, table=True):
    __tablename__ = "users"

    telegram_username: Optional[str] = Field(nullable=True)
    first_name: str = Field(nullable=False)
    last_name: Optional[str] = Field(nullable=True)
    language_code: Optional[str] = Field(nullable=True)

    is_active: bool = Field(default=True)

    last_interaction: Optional[datetime] = Field(nullable=True)
    chat_id: int = Field(nullable=False)

    email: Optional[EmailStr] = Field(nullable=True)
    phone_number: Optional[str] = Field(nullable=True)
    timezone: Optional[str] = Field(
        nullable=True,
    )

    command_count: int = Field(default=0)
    is_blocked: bool = Field(default=False)
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
            return f"{self.size * constants.KB)kb"
        if self.unit == FileSize.MegaBytes:
            return f"{self.size * constants.MB}mb"


class DocumentEmbeddings(BaseModel, table=True):
    __tablename__ = "document_embeddings"
    text: str = Field(nullable=False)
    embedding: Any = Field(sa_type=Vector(1024))
    page_number: int = Field(nullable=False)
    document: "Documents" = Relationship(back_populates="embedding")
