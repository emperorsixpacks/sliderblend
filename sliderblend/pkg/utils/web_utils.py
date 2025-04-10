from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from fastapi.templating import Jinja2Templates

from sliderblend.pkg.constants import TG_INITDATA_LIFESPAN
from sliderblend.pkg.types import error, Error

if TYPE_CHECKING:
    from starlette.datastructures import URL

    from sliderblend.pkg.settings import WebAppSettings
    from sliderblend.pkg.types import TelegramInitData


def get_templates(settings: WebAppSettings) -> Jinja2Templates:
    # Lazy import to avoid circular dependency

    return Jinja2Templates(directory=settings.TEMPLATES_DIR)


@dataclass(kw_only=True)
class PageContext:
    request: Any
    active_page: int
    total_pages: int | None = None
    next_step: URL | None = None
    previous_step: URL | None = None
    show_navigation: bool = True

    def dict(self):
        # Get all instance attributes (not class attributes or methods)
        return self.__dict__


def verify_tg_init_data(
    init_data: TelegramInitData, bot_token: str
) -> TelegramInitData | error:
    """
    Verify Telegram initData and return user data if valid.

    Args:
        init_data (str): The initData string from Telegram.WebApp.initData
        bot_token (str): Your bot token from BotFather

    Returns:
        dict: User data if verified, or raises ValueError if invalid
    """

    exp_date = datetime.fromtimestamp(init_data.auth_date) + timedelta(
        seconds=TG_INITDATA_LIFESPAN
    )

    if exp_date < datetime.now():
        return None, Error(message="Data expired")

    # Generate secret key from bot token
    secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256)
    computed_hash = hmac.new(
        secret_key.digest(), init_data.to_string().encode(), hashlib.sha256
    )
    # Verify the hash
    if hmac.compare_digest(computed_hash.hexdigest(), init_data.res_hash):
        # Extract and parse user data
        return init_data

    return None, Error(message="Invalid data")



# TODO write tests
