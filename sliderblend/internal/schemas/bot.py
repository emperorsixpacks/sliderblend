from pydantic import BaseModel, ConfigDict


class BotRequestSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_telegram_id: str


class BotChunkRequestSchema(BotRequestSchema):
    file_id: str
    size: int
    number_of_pages: int
