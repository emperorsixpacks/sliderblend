from uuid import UUID

from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field

from sliderblend.internal.schemas.base import BaseSchema


class CreateDocumentSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True, strict=True)
    document_name: str
    size: int
    user_id: UUID
    number_of_pages: int


class GetDocumentSchema(BaseSchema):
    document_id: UUID = Field(alias="id")
    document_name: str
    size: int
    user_id: UUID


class CreateDocumentEmbeddingSchema(BaseModel):
    document: list[Document]
    embedding: list[list[float]]
    document_id: UUID

    def get_documents(self) -> list[list[Document, list[float]]]:
        return list(zip(self.document, self.embedding))
