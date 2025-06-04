from datetime import datetime
from typing import Any, Optional, Self, Tuple
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Field, Session, SQLModel

from sliderblend.pkg import get_logger
from sliderblend.pkg.types import Error, error

logger = get_logger(__name__)


class DatabaseMixin:
    def create(self, session: Session) -> Tuple[Optional[Self], error]:
        err = self.save(session)
        if err:
            return None, err
        return self, None

    def save(self, session: Session) -> error:
        try:
            session.add(self)
            session.flush()
            session.refresh(self)
            return None
        except IntegrityError as e:
            session.rollback()
            logger.error(e, stack_info=True)
            return Error()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(e, stack_info=True) 
            return Error()

    @classmethod
    def get(
        cls, *, field: str = "id", value: Any, session: Session
    ) -> Tuple[Optional[Self], error]:
        field_attr = getattr(cls, field, None)

        if field_attr is None:
            return None, Error(f"Field '{field}' does not exist in the model.")
        user = session.query(cls).filter(field_attr == value).first()

        if user:
            return user, None
        return None, Error(f"User with {field} = {value} not found")

    @classmethod
    def exists(cls, *, field: str = "id", value: Any, session: Session) -> bool:
        _, err = cls.get(field=field, value=value, session=session)
        return err is not None


class BaseModel(SQLModel, DatabaseMixin):
    model_config = ConfigDict(
        use_enum_values=True, validate_assignment=True, populate_by_name=True
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )
