from os import name

from fastapi import APIRouter, Request

from sliderblend.pkg import utils
from sliderblend.pkg.settings import WebAppSettings

TOTAL_PAGES = 4
settings = WebAppSettings()

templates = utils.get_templates(settings)

gen_router = APIRouter(prefix="/steps")


@gen_router.get("/")
def get_started(request: Request):
    context = utils.PageContext(
        next_step=request.url_for("upload_document"),
        request=request,
        active_page=1,
    ).dict()
    return templates.TemplateResponse(
        "home.html",
        context,
    )


@gen_router.get("/upload-document")
async def upload_document(request: Request):
    context = utils.PageContext(
        request=request,
        active_page=1,
        total_pages=TOTAL_PAGES,
        show_navigation=False,
        next_step=request.url_for("upload_document"),
    ).dict()
    return templates.TemplateResponse(
        "steps/step_1.html",
        context,
    )


@gen_router.get("/configure-presntation")
async def config_presentation(request: Request):
    context = utils.PageContext(
        request=request,
        active_page=2,
        total_pages=TOTAL_PAGES,
        previous_step=request.url_for("upload_document"),
        next_step=request.url_for("view_slides"),
    ).dict()
    return templates.TemplateResponse("steps/step_2.html", context)


@gen_router.get("/view-slides")
async def view_slides(request: Request):
    context = utils.PageContext(
        request=request,
        active_page=3,
        total_pages=TOTAL_PAGES,
        previous_step=request.url_for("config_presentation"),
        next_step=request.url_for("preview_slides"),
    ).dict()
    return templates.TemplateResponse("steps/step_3.html", context)


@gen_router.get("/preview")
async def preview_slides(request: Request):
    context = utils.PageContext(
        request=request,
        active_page=4,
        total_pages=TOTAL_PAGES,
        show_navigation=False,
        next_step=request.url_for("view_slides"),
    ).dict()
    return templates.TemplateResponse("steps/step_4.html", context)
