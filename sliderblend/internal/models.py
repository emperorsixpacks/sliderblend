from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Tuple, Self
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from pydantic import ConfigDict, EmailStr, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Field, Relationship, Session, SQLModel

from sliderblend.pkg import KB, MB
from sliderblend.pkg.types import Error, error


class FileSize(Enum):
    KiloBytes = 0
    MegaBytes = 1


class DatabaseMixin:
    def create(self, session: Session) -> Tuple[Optional[Self], error]:
        err = self.save(session)
        if err:
            return None, err
        return self, None

    def save(self, session: Session) -> error:
        try:
            session.add(self)
            session.flush()
            session.refresh(self)
            return None
        except IntegrityError as e:
            session.rollback()
            return Error(message=str(e.orig).split("\n")[0])
        except SQLAlchemyError as e:
            session.rollback()
            return Error(message=str(e.orig))

    @classmethod
    def get(
        cls, *, field: str = "id", value: Any, session: Session
    ) -> Tuple[Optional[Self], error]:
        field_attr = getattr(cls, field, None)

        if field_attr is None:
            return None, Error(f"Field '{field}' does not exist in the model.")
        user = session.query(cls).filter(field_attr == value).first()

        if user:
            return user, None
        return None, Error(f"User with {field} = {value} not found")

    @classmethod
    def exists(cls, *, field: str = "id", value: Any, session: Session) -> bool:
        _, err = cls.get(field=field, value=value, session=session)
        return err is not None


class BaseModel(SQLModel, DatabaseMixin):
    model_config = ConfigDict(
        use_enum_values=True, validate_assignment=True, populate_by_name=True
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )


class UserModel(BaseModel, table=True):
    __tablename__ = "users"

    telegram_username: str = Field(unique=True)
    telegram_user_id: str = Field(unique=True)
    first_name: str
    last_name: Optional[str] = Field(nullable=True)
    language_code: Optional[str] = Field(nullable=True)

    is_active: bool = Field(default=True)

    last_interaction: Optional[datetime] = Field(nullable=True)
    chat_id: int = Field(nullable=True)

    email: Optional[EmailStr] = Field(nullable=True)
    phone_number: Optional[str] = Field(nullable=True)
    timezone: Optional[str] = Field(
        nullable=True,
    )

    #   command_count: int = Field(default=0)
    is_blocked: bool = Field(default=False)
    documents: List["DocumentsModel"] = Relationship(back_populates="user")

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


class DocumentsModel(BaseModel, table=True):
    __tablename__ = "documents"
    number_of_pages: int = Field(nullable=False)
    size: int = Field(nullable=False)
    unit: FileSize = Field(nullable=False)
    is_embedded: bool = Field(default=False, nullable=False)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE", nullable=False)
    user: "UserModel" = Relationship(back_populates="documents")
    embedding: Optional["DocumentEmbeddingsModel"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"uselist": False},  # Ensures one-to-one
    )

    def get_size_in_unit(self) -> str:
        if self.unit == FileSize.KiloBytes:
            return f"{self.size * KB}kb"
        if self.unit == FileSize.MegaBytes:
            return f"{self.size * MB}mb"


class DocumentEmbeddingsModel(BaseModel, table=True):
    __tablename__ = "document_embeddings"
    text: str = Field(nullable=False)
    embedding: Any = Field(sa_type=Vector(1024))
    page_number: int = Field(nullable=False)
    document: "DocumentsModel" = Relationship(back_populates="embedding")
    document_id: UUID = Field(
        foreign_key="documents.id", ondelete="CASCADE", nullable=False
    )
