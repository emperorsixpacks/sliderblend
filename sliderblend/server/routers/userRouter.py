from fastapi import APIRouter, Depends

from sliderblend.internal.schemas import UserCache
from sliderblend.pkg import get_logger
from sliderblend.server.dependencies import get_current_user

PREFIX = "/user"
logger = get_logger(__name__)


class UserRouter:
    def get_router(self):
        router = APIRouter(prefix=PREFIX)
        router.add_api_route("/me", self.get_user, methods=["GET"])
        return router

    async def get_user(
        self,
        current_user: UserCache = Depends(get_current_user),
    ):
        return current_user.model_dump()
