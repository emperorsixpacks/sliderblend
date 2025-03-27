from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from sliderblend import LLMSettings 
llm_settings = LLMSettings()

model = OpenAIModel(
    llm_settings.llm_name,
    base_url="https://openrouter.ai/api/v1",
    api_key=llm_settings.llm_api_key,
)
