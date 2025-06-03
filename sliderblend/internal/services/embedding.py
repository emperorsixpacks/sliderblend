from __future__ import annotations

import io
from typing import IO, List, Union

import fitz
from cohere import AsyncClient, Client

from sliderblend.pkg import CohereSettings, get_logger
from sliderblend.pkg.utils import exists

cohere_settings = CohereSettings()
logger = get_logger(__name__)

type EMBEDDING_MODEL = Union[Client, AsyncClient]


# TODO we need to fix this to load multiple documents
# TODO we need to load, return the file contents as well as the number of pages, the file size and unit


class LoadPDF:
    def __init__(self, source: Union[str, IO[bytes]]) -> None:
        self.source = source

    def read(self):
        contents: str = ""

        if isinstance(self.source, str):
            if not exists(self.source):
                logger.error("could not open file %s", self.source)
                raise FileNotFoundError(f"Prompt {self.source} does not exist")
            doc = fitz.open(self.source)
        elif isinstance(self.source, io.IOBase):
            # Assumes binary mode (rb) if it's a file-like object
            doc = fitz.open(stream=self.source.read(), filetype="pdf")
        else:
            raise TypeError("Source must be a file path or a file-like object")

        with doc:
            for page in doc:
                contents += page.get_text()
        return contents


# This function exclusively uses Cohere's embedding model to embed documents.
# It processes the input document in batches and returns float embeddings.
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
