from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, Header, HTTPException, Request, status

from sliderblend.internal.schemas import UserCache
from sliderblend.pkg import ClientSettings, get_logger
from sliderblend.pkg.types import Error

if TYPE_CHECKING:
    from sliderblend.internal import RedisClient

logger = get_logger(__name__)


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


def get_clients(request: Request) -> ClientSettings:
    return request.app.state.clients


def get_redis(clients: ClientSettings = Depends(get_clients)):
    return clients.REDIS_CLIENT


def get_redis_job(clients: ClientSettings = Depends(get_clients)):
    return clients.REDIS_JOB_CLIENT


def get_cohere(clients: ClientSettings = Depends(get_clients)):
    return clients.COHERE_CLIENT


def get_ibm(clients: ClientSettings = Depends(get_clients)):
    return clients.IBM_CLIENT


def get_session(request: Request, key: ReqSession = Depends()) -> ReqSession:
    return key(request)


async def get_current_user(
    session_key: str = Depends(get_session),
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
