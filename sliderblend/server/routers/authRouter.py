from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from sliderblend.internal.models import UserModel
from sliderblend.internal.schemas import UserCache
from sliderblend.pkg import get_logger, get_session
from sliderblend.pkg.utils import generate_session_key, verify_tg_init_data
from sliderblend.server.dependencies import get_redis

if TYPE_CHECKING:
    from sqlmodel import Session

    from sliderblend.internal import RedisClient
    from sliderblend.pkg import TelegramSettings


AUTH_PREFIX = "/auth"
AUTH_TELEGRAM_PATH = "/telegram"
logger = get_logger(__name__)


class AuthRouter:
    def __init__(
        self,
        telegram_settings: TelegramSettings,
    ) -> None:
        self.telegram_settings = telegram_settings

    def get_router(self):
        router = APIRouter(prefix=AUTH_PREFIX)
        router.add_api_route(AUTH_TELEGRAM_PATH, self.callback_url, methods=["POST"])
        return router

    async def callback_url(
        self,
        data: dict,
        redis_client: RedisClient = Depends(get_redis),
        session: Session = Depends(get_session),
    ):
        logger.info("Received callback request with data")

        # Verify Telegram init data
        init_data = data["initData"]
        logger.debug("Parsed init data")

        tg_data, err = verify_tg_init_data(
            init_data, self.telegram_settings.telegram_bot_token
        )
        if err:
            logger.warning("Telegram init data verification failed: %s", err.message)
            return JSONResponse(
                content=err.message, status_code=status.HTTP_403_FORBIDDEN
            )

        # Process user data
        user_data = tg_data.user
        logger.info(
            "Processing user data for Telegram user ID: %s",
            user_data.telegram_user_id,
        )

        user, err = UserModel.get(
            field="telegram_user_id",
            value=str(user_data.telegram_user_id),
            session=session,
        )

        if err:
            logger.info(
                "New user detected, creating account for Telegram user ID: %s",
                user_data.telegram_user_id,
            )
            user = UserModel(
                chat_instance=tg_data.chat_instance,
                chat_type=tg_data.chat_type,
                **user_data.model_dump(),
            )
            if err := user.create_user(session):
                logger.error(f"Failed to create user: {err.message}")
                return JSONResponse(
                    content=err.message, status_code=status.HTTP_403_FORBIDDEN
                )

        # Generate session
        session_key = generate_session_key(user.id)
        logger.debug("Generated session key")

        err = await redis_client.create(
            f"user:{session_key}", UserCache(**user.model_dump())
        )
        if err:
            logger.error("Failed to create Redis session: %s", err.message)
            return JSONResponse(
                content=err.message,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        session.commit()
        logger.info("Successfully processed callback for user ID: %s", user.id)
        return {"session": session_key}
