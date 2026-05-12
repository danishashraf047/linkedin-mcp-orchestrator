from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings
from app.utils.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="LinkedIn MCP Content Automation",
    version="1.0.0",
    description="AI-assisted LinkedIn content generation, validation, image handling, custom API delivery, and LinkedIn publishing.",
)

settings.local_storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=settings.local_storage_dir), name="images")
app.include_router(router, prefix="/api")
