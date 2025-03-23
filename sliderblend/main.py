import asyncio
import os

import dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from sliderblend.utils import BASE_DIR


dotenv.load_dotenv(os.path.join(BASE_DIR, ".env"))
model = OpenAIModel(
    os.getenv("OPENROUTER_MODEL"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API"),
)
agent = Agent(model)
result = asyncio.run(agent.run("Who is the president of america"))
print(result)
