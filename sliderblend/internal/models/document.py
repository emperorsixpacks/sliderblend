from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship

from sliderblend.internal.models.base import BaseModel
from sliderblend.pkg import KB, MB
from sliderblend.pkg.types import FileSize


class DocumentsModel(BaseModel, table=True):
    __tablename__ = "documents"
    number_of_pages: int = Field(nullable=False)
    document_name: str = Field(nullable=False)
    size: int = Field(nullable=False)
    unit: FileSize = Field(nullable=False)
    is_embedded: bool = Field(default=False, nullable=False)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE", nullable=False)

    def get_size_in_unit(self) -> str:
        if self.unit == FileSize.KiloBytes:
            return f"{self.size * KB}kb"
        if self.unit == FileSize.MegaBytes:
            return f"{self.size * MB}mb"
        return None


class DocumentEmbeddingsModel(BaseModel, table=True):
    __tablename__ = "document_embeddings"
    text: str = Field(nullable=False)
    embedding: Any = Field(sa_type=Vector(1024))
    page_number: int = Field(nullable=False)
    document_id: UUID = Field(
        foreign_key="documents.id", ondelete="CASCADE", nullable=False
    )
