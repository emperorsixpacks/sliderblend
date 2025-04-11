from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    created_data: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
    
    def __setattr__(self, name, value):
        """Update the updated_date whenever any field changes"""
        if name != "updated_date" and hasattr(self, name):
            super().__setattr__("updated_date", datetime.now())
        super().__setattr__(name, value)

class SessionData(BaseSchema):
    key: str

    def return_key(self) -> str:
        return f"user:{self.key}"


class UserCache(BaseSchema):
    telegram_username: str
    telegram_user_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    is_active: bool
