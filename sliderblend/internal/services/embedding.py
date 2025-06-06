from __future__ import annotations

import io
from typing import IO, List, Union

import fitz
from cohere import AsyncClient, Client
from langchain_community.embeddings.cohere import CohereEmbeddings
from langchain_core.documents import Document

from sliderblend.pkg import CohereSettings, get_logger
from sliderblend.pkg.types import Error, error

cohere_settings = CohereSettings()
logger = get_logger(__name__)

type EMBEDDING_MODEL = Union[Client, AsyncClient]


class LoadPDF:
    def __init__(self, name: str, source: Union[str, IO[bytes]]) -> None:
        self.source = source
        self.name = name

    def load(self) -> tuple[list[Document], error]:
        docs = []

        if not isinstance(self.source, io.IOBase):
            err = Error("Error: Only supports io.IOBase")
            return None, err

        doc = fitz.open(stream=self.source, filetype="pdf")
        for i, page in enumerate(doc):
            text = page.get_text()
            metadata = {"source": self.name, "page": i+1}
            docs.append(Document(page_content=text, metadata=metadata))
        return docs, None


async def embed_document(
    embedding_model: EMBEDDING_MODEL, *, document: List[str], batch_size: int
):
    all_embeddings = []

    # Split document into batches
    batches = [
        document[i : i + batch_size] for i in range(0, len(document), batch_size)
    ]
    logger.info("Starting embedding")
    for batch in batches:
        logger.info("Starting embedding on batch")
        embeddings = await embedding_model.embed(
            model="embed-english-v3.0",
            input_type="search_document",
            embedding_types=["float"],
            texts=batch,
        )
        all_embeddings.extend(embeddings.embeddings.float)

    logger.info("Done embedding")
    return all_embeddings
