from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sliderblend.internal import UserModel
from sliderblend.pkg import get_session
from sliderblend.pkg.types import TelegramInitData
from sliderblend.pkg.utils import generate_session_key, verify_tg_init_data
from sliderblend.web.schema import SessionData, UserCache

if TYPE_CHECKING:
    from sqlmodel import Session

    from sliderblend.internal import RedisClient
    from sliderblend.pkg import TelegramSettings


CALLBACK_PATH = "/callback"


class AuthRouter:
    def __init__(
        self, telegram_settings: TelegramSettings, redis_client: RedisClient
    ) -> None:
        self.telegram_settings = telegram_settings
        self.redis_client = redis_client

    def get_router(self):
        router = APIRouter(prefix="/auth")
        router.add_api_route(CALLBACK_PATH, self.callback_url, methods=["POST"])
        return router

    def callback_url(self, data: dict, session: Session = Depends(get_session)):
        init_data = TelegramInitData.from_string(data["initData"])
        data, err = verify_tg_init_data(
            init_data, self.telegram_settings.telegram_bot_token
        )
        if err:
            print(err.message)
            return JSONResponse(
                content=err.message, status_code=status.HTTP_403_FORBIDDEN
            )
        user_data = init_data.user
        user, err = UserModel.get(
            field="telegram_user_id",
            value=str(user_data.telegram_user_id),
            session=session,
        )
        if err:
            user = UserModel(**user_data.model_dump())
            if err := user.create_user(session):
                print(err.message)
                return JSONResponse(
                    content=err.message, status_code=status.HTTP_403_FORBIDDEN
                )
        session.commit()
        session_key = generate_session_key(user)
        _, err = self.redis_client.create(
            f"user:{session_key}", UserCache(**user.model_dump())
        )
        if err:
            print(err.message)
            return JSONResponse(
                content=err.message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return {"session": session_key}
