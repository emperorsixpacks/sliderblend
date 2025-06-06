from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from sliderblend.internal.models import UserModel
from sliderblend.internal.schemas import BotRequestSchema, UserCache
from sliderblend.pkg import AppSecret, ClientSettings, get_logger, get_session
from sliderblend.pkg.types import Error
from sliderblend.pkg.utils import verifiy_payload

if TYPE_CHECKING:
    from sliderblend.internal import RedisClient

logger = get_logger(__name__)
app_secret = AppSecret()


class ReqSession:
    """
    session authorisation handler
    """

    def __call__(self, request: Request) -> str:
        session_key = request.headers.get("X-Session-Key")
        if session_key is None:
            err = Error("Unauthorised request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=err.message
            )
        return session_key


class ReqBotSession:
    """
    session authorisation handler
    """

    def __call__(self, request: Request) -> str:
        signature = request.headers.get("X-Signature")
        if signature is None:
            err = Error("Unauthorised request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=err.message
            )
        return signature


def get_clients(request: Request) -> ClientSettings:
    return request.app.state.clients


def get_redis(clients: ClientSettings = Depends(get_clients)):
    return clients.REDIS_CLIENT


def get_redis_job(clients: ClientSettings = Depends(get_clients)):
    return clients.REDIS_JOB


def get_cohere(clients: ClientSettings = Depends(get_clients)):
    return clients.COHERE_CLIENT


def get_ibm(clients: ClientSettings = Depends(get_clients)):
    return clients.IBM_CLIENT


def get_client_session(request: Request, key: ReqSession = Depends()) -> ReqSession:
    return key(request)


async def get_current_user(
    session_key: str = Depends(get_client_session),
    redis_client: RedisClient = Depends(get_redis),
) -> UserCache:
    if not session_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Not found"
        )
    user, err = await redis_client.get(session_key, UserCache)
    if err:
        logger.error(err.message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Not found"
        )
    return user


async def veifiy_bot_request(
    request: Request, req_signature: ReqBotSession = Depends()
) -> BotRequestSchema:
    signature = req_signature(request)
    payload = await request.json()
    if not verifiy_payload(app_secret.app_secret, signature, payload):
        err = Error("Invalid signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=err.message
        )
    return BotRequestSchema.model_validate(payload)


async def get_bot_req_user(
    user: BotRequestSchema = Depends(veifiy_bot_request),
    redis_cache: RedisClient = Depends(get_redis),
    session: Session = Depends(get_session),
) -> UserCache:
    cache_key = f"user:{user.user_telegram_id}"

    # Try to get user from cache
    cached_user, _ = await redis_cache.get(cache_key, UserCache)
    if cached_user:
        logger.info(f"User {user.user_telegram_id} retrieved from cache.")
        return cached_user

    # Fallback to DB
    logger.info(f"User {user} not found in cache. Querying database...")
    user, err = UserModel.get(
        field="telegram_user_id", value=user.user_telegram_id, session=session
    )
    if err:
        logger.warning(f"User {user} not found in database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Store in cache for future
    await redis_cache.create(cache_key, user)
    logger.info(f"User {user} cached for future requests.")

    return user
