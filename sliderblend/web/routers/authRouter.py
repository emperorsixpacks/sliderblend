from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sliderblend.internal import UserModel
from sliderblend.pkg import get_session
from sliderblend.pkg.types import TelegramInitData
from sliderblend.pkg.utils import verify_tg_init_data

if TYPE_CHECKING:
    from sqlmodel import Session

    from sliderblend.pkg import TelegramSettings


CALLBACK_PATH = "/callback"


class AuthRouter:
    def __init__(self, telegram_settings: TelegramSettings) -> None:
        self.telegram_settings = telegram_settings

    def get_router(self):
        router = APIRouter(prefix="/auth")
        router.add_api_route(CALLBACK_PATH, self.callback_url)
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
        _, err = UserModel.get(
            field="telegram_user_id",
            value=str(user_data.telegram_user_id),
            session=session,
        )
        if err:
            new_user = UserModel(**user_data.model_dump())
            err = new_user.create_user(session)
            if err:
                print(err.message)
                return JSONResponse(
                    content=err.message, status_code=status.HTTP_403_FORBIDDEN
                )
        session.commit()

        return {"ok": True}
