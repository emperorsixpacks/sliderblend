from dataclasses import dataclass
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.together import TogetherProvider

from sliderblend.pkg import LLMSettings

llm_settings = LLMSettings()

model = OpenAIModel(
    llm_settings.llm_name,
    provider=TogetherProvider(api_key=llm_settings.llm_api_key),
)
