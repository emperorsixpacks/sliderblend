from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sliderblend.pkg import WebAppSettings

app_settings = WebAppSettings()

app = FastAPI()

app.mount("/static", StaticFiles(directory=app_settings.STATIC_DIR), name="static")


templates = Jinja2Templates(directory=app_settings.TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")
