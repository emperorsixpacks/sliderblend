from uuid import UUID

from pydantic import BaseModel, Field

from sliderblend.internal.schemas.base import BaseSchema
from sliderblend.pkg.types import FileSize


class CreateDocumentSchema(BaseModel):
    document_name: str
    size: int
    unit: FileSize
    user_id: UUID


class GetDocumentSchema(BaseSchema):
    document_id: UUID = Field(alias="id")
    document_name: str
    size: int
    unit: FileSize
    user_id: UUID
