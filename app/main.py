import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import dataset_service, router, similarity_service
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.services.nlp_service import NLPService
from app.utils.logging import configure_logging

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        dataset_service.sync_from_csv(db)
        projects = dataset_service.fetch_all_projects(db)
        similarity_service.build_index(projects, preprocess_fn=NLPService.preprocess)
        logger.info("PCAS backend startup completed.")
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    return FileResponse(INDEX_FILE)


app.include_router(router)
