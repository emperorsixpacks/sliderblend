from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from sliderblend.pkg import WebAppSettings
from sliderblend.web.routes import gen_router

app_settings = WebAppSettings()
app = FastAPI()
app.mount("/static", StaticFiles(directory=app_settings.STATIC_DIR), name="static")


@app.get("/")
async def home(request: Request):
    upload_url = request.url_for("upload_document")
    return RedirectResponse(upload_url)


app.include_router(gen_router)
