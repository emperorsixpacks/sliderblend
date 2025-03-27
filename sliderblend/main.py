import asyncio
import os

import cohere
import dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from sqlmodel import SQLModel, create_engine

from sliderblend.logger import get_logger
from sliderblend.utils import BASE_DIR, LoadPDF, Prompt

dotenv.load_dotenv(os.path.join(BASE_DIR, ".env"))
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('VECTOR_DB_USERNAME')}:{os.getenv('VECTOR_DB_PASSWORD')}@{os.getenv('VECTOR_DB_HOST')}:{os.getenv('VECTOR_DB_PORT')}/{os.getenv('VECTOR_DB')}"
NUMBER_OF_SLIDES = 5
BASE_PROMPT = "base_system_prompt"
BATCH_SIZE = 96
logger = get_logger()

system_prompt = Prompt(BASE_PROMPT, number_of_slides=NUMBER_OF_SLIDES, tone="cheerful")
engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL statements
# Create the tables (if they don’t exist)
model = OpenAIModel(
    os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_MODEL"),
)

# agent = Agent(model, system_prompt=system_prompt.read())
# agent.run_sync("Generate presentations")


embedding_model = cohere.AsyncClient(os.getenv("COHERE_API_KEY"))

