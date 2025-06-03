from datetime import datetime

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    created_data: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)

    def __setattr__(self, name, value):
        """Update the updated_date whenever any field changes"""
        if name != "updated_date" and hasattr(self, name):
            super().__setattr__("updated_date", datetime.now())
        super().__setattr__(name, value)
