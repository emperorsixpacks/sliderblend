from __future__ import annotations
from uuid import UUID
from typing import Optional, Tuple, TypeVar, TYPE_CHECKING
import uuid

from models import UserModel, DocumentsModel  # Assuming UserModel is in a separate module
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from sliderblend.pkg.types import error, Error

if TYPE_CHECKING:
    from sliderblend.

T = TypeVar("T")


# Function to get a user by their telegram_user_id
def get_user_by_telegram_user_id(
    db: Session, telegram_user_id: str
) -> Optional[UserModel]:
    try:
        return (
            db.query(UserModel)
            .filter(UserModel.telegram_user_id == telegram_user_id)
            .one()
        )  # Will raise NoResultFound if no match
    except NoResultFound:
        return None


# Function to check if a user exists by telegram_user_id
def user_exists(db: Session, telegram_user_id: str) -> bool:
    user = get_user_by_telegram_user_id(db, telegram_user_id)
    return user is not None


# Function to update last interaction
def update_last_interaction(db: Session, telegram_user_id: str) -> Optional[UserModel]:
    user = get_user_by_telegram_user_id(db, telegram_user_id)
    if user:
        user.update_last_interaction()  # This sets the current time as the last interaction
        db.commit()  # Commit the update to the database
        db.refresh(user)  # Refresh to get the updated data
        return user
    return None


