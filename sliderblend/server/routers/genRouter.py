from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from sliderblend.pkg import utils

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

    from sliderblend.pkg import WebAppSettings


class GenRouter:
    def __init__(
        self,
        *,
        templates: Jinja2Templates,
        web_app_settings: WebAppSettings,
        total_pages: int,
    ):
        self.templates = templates
        self.web_app_settings = web_app_settings
        self.total_pages = total_pages

    def get_router(self) -> APIRouter:
        router = APIRouter(prefix="/steps")

        router.add_api_route(
            "/upload-document", self.upload_document, methods=["GET", "POST"]
        )
        router.add_api_route(
            "/configure-presntation", self.config_presentation, methods=["GET", "POST"]
        )
        router.add_api_route("/view-slides", self.view_slides, methods=["GET", "POST"])
        router.add_api_route("/preview", self.preview_slides, methods=["GET", "POST"])

        return router

    def upload_document(self, request: Request) -> HTMLResponse:
        context = utils.PageContext(
            request=request,
            active_page=1,
            total_pages=self.total_pages,
            show_navigation=False,
            next_step=request.url_for("upload_document"),
        ).dict()
        return self.templates.TemplateResponse("steps/step_1.html", context)

    def config_presentation(self, request: Request) -> HTMLResponse:
        context = utils.PageContext(
            request=request,
            active_page=2,
            total_pages=self.total_pages,
            previous_step=request.url_for("upload_document"),
            next_step=request.url_for("view_slides"),
        ).dict()
        return self.templates.TemplateResponse("steps/step_2.html", context)

    def view_slides(self, request: Request) -> HTMLResponse:
        context = utils.PageContext(
            request=request,
            active_page=3,
            total_pages=self.total_pages,
            previous_step=request.url_for("config_presentation"),
            next_step=request.url_for("preview_slides"),
        ).dict()
        return self.templates.TemplateResponse("steps/step_3.html", context)

    def preview_slides(self, request: Request) -> HTMLResponse:
        context = utils.PageContext(
            request=request,
            active_page=4,
            total_pages=self.total_pages,
            show_navigation=False,
            next_step=request.url_for("view_slides"),
        ).dict()
        return self.templates.TemplateResponse("steps/step_4.html", context)
