from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector  # Assuming you're using pgvector
from sqlmodel import Field, SQLModel
from sqlacl


class BaseModel(SQLModel):
    id: UUID = Field(default_factory=lambda x: str(uuid4()), primary_key=True)
    created_date: datetime = Field(default_factory=datetime.now())



class User(BaseModel, table=True):
    __tablename__ = "users"

    telegram_username: Optional[str] = Filed(String(32), nullable=True, 
                                                    comment="Telegram username (if set)")
    first_name: str = Filed(String(64), nullable=False, 
                                   comment="User's first name from Telegram")
    last_name: Optional[str] = Filed(String(64), nullable=True, 
                                            comment="User's last name from Telegram")
    language_code: Optional[str] = Filed(String(10), nullable=True, 
                                                comment="User's language code (e.g., 'en')")

    is_active: bool = Filed(Boolean, default=True, 
                                   comment="Whether the user is currently active")

    last_interaction: Optional[datetime] = Filed(DateTime, nullable=True, 
                                                        comment="Last time user interacted with bot")
    chat_id: int = Filed(Integer, nullable=False, 
                                comment="Telegram chat ID for messaging")

    email: Optional[EmailStr] = Filed(String(255), nullable=True, 
                                             comment="User's email address")
    phone_number: Optional[str] = Filed(String(20), nullable=True, 
                                               comment="User's phone number")
    timezone: Optional[str] = Filed(String(50), nullable=True, 
                                           comment="User's timezone (e.g., 'UTC', 'America/New_York')")

    # Bot usage tracking
    command_count: int = Filed(Integer, default=0, 
                                      comment="Number of commands executed by user")
    is_blocked: bool = Filed(Boolean, default=False, 
                                    comment="Whether the user is blocked from using the bot")

    # Pydantic configuration for validation
    class Config:
        orm_mode = True  # Enables compatibility with SQLAlchemy ORM

    # Optional: Method to update last interaction
    def update_last_interaction(self):
        self.last_interaction = datetime.now()

class Documents(BaseModel, table=True):
    pass

class DocumentEmbeddings(BaseModel, table=True):
    __tablename_ = "users"
    text: str
    embedding: Any = Field(sa_type=Vector(1024))  # Vector field for embeddings
