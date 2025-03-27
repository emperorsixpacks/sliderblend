from typing import List

import cohere
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sliderblend import get_logger, CohereSettings, utils, types

cohere_settings = CohereSettings()
logger = get_logger()

RECURSIVESPLITTER = RecursiveCharacterTextSplitter(
    ["\n\n", "\n", "."], chunk_size=1500, chunk_overlap=500
)

EMBEDDING_MODEL = cohere.AsyncClient(cohere_settings.cohere_api_key)


# TODO we need to fix this to load multiple documents
class LoadPDF:
    def __init__(self, file_name: str) -> None:
        self.file = file_name

    def read(self):
        contents: str = ""
        if not utils.exists(self.file):
            logger.error("could not open file %s", self.file)
            raise FileNotFoundError(f"Prompt {self.file} does not exist")
        with fitz.open(self.file) as document:
            for page in document:
                contents += page.get_text()
        return contents


# This function exclusively uses Cohere's embedding model to embed documents.
# It processes the input document in batches and returns float embeddings.
async def embed_document(
    embedding_model: types.EmbeddingModel, *, document: List[str], batch_size: int
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
