from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from sliderblend.internal.models import (
    DocumentEmbeddingsModel,
    DocumentsModel,
    UserModel,
)
from sliderblend.internal.schemas import CreateDocumentEmbeddingSchema
from sliderblend.pkg.types import Error, error

if TYPE_CHECKING:
    from sqlmodel import Session

    from sliderblend.internal.schemas import CreateDocumentSchema


def create_document(
    schema: CreateDocumentSchema, db: Session
) -> Tuple[Optional[DocumentsModel], error]:
    user, err = UserModel.get(value=schema.user_id, session=db)
    if err:
        return None, Error(f"User {(schema.user_model)} does not exist")

    if not user.is_active or user.is_blocked:
        return None, Error("User is inactive or has been blocked")

    document, err = DocumentsModel.model_validate(schema).create(db)
    if err:
        return None, err
    return document, None


def create_document_embedding(
    schema: CreateDocumentEmbeddingSchema, db: Session
) -> Optional[error]:
    # Validate related document exists
    document, err = DocumentsModel.get(value=schema.document_id, session=db)
    if err or document is None:
        return None, Error(f"Document with id {schema.document_id} does not exist")

    docs = schema.get_documents()

    for doc in docs:
        document_page, embedding_vector = doc
        embedding_model = DocumentEmbeddingsModel(
            text=document_page.page_content,
            embedding=embedding_vector,
            page_number=document_page.metadata["page"],
            document_id=schema.document_id,
        )
        _, err = embedding_model.create(db)
        if err:
            return err

    return None
