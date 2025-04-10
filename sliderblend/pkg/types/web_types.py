import json
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Base(BaseModel):
    model_config = ConfigDict(extra="allow", from_attributes=True)

    @classmethod
    def from_string(cls, init_data_str: str) -> "TelegramInitData":
        """Parse initData string into a TelegramInitData object."""
        # Parse the URL-encoded string
        parsed_data = {
            k: unquote(v)
            for k, v in [s.split("=", 1) for s in init_data_str.split("&")]
        }
        parsed_data["user"] = json.loads(parsed_data["user"])

        # Create and return the TelegramInitData object
        return cls.from_orm(parsed_data)

    def to_string(self) -> str:
        """Convert the model fields into a string of key-value pairs."""
        lines = []
        for key, value in self.model_dump(by_alias=True).items():
            # Format as "key": "value" (strings get quoted, others don’t)
            lines.append(f"{key}={value}")
        return (
            "\n".join(sorted(lines))
            .replace("/", r"\/")
            .replace("'", r'"')
            .replace(" ", "")
            .replace('"true"', "true")
            .strip()
        )


class TelegramUser(Base):
    user_id: int = Field(alias="id")
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    allows_write_to_pm: str
    photo_url: str

    @field_validator("allows_write_to_pm", mode="before")
    @classmethod
    def convert_to_str(cls, value: str):
        return str(value).lower()


class TelegramInitData(Base):
    user: TelegramUser
    chat_instance: str
    chat_type: str
    auth_date: int
    signature: str
    res_hash: str = Field(alias="hash", exclude=True)
