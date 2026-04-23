import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import get_settings
from app.core.database import get_db
from app.models.schemas import AnalysisResponse, AnalyzeTextRequest
from app.services.analysis_service import AnalysisService
from app.services.dataset_service import DatasetService
from app.services.similarity_service import SimilarityService

router = APIRouter()
logger = logging.getLogger(__name__)

settings = get_settings()
dataset_service = DatasetService()
similarity_service = SimilarityService()
analysis_service = AnalysisService(similarity_service=similarity_service)


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    project_count = len(dataset_service.fetch_all_projects(db))
    return {"status": "ok", "projects_indexed": project_count}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: Request, db: Session = Depends(get_db)) -> AnalysisResponse:
    content_type = request.headers.get("content-type", "")
    logger.info("Received /analyze request with content-type=%s", content_type)

    if "application/json" in content_type:
        payload = AnalyzeTextRequest.model_validate(await request.json())
        return analysis_service.analyze_text(
            title=payload.title,
            abstract=payload.abstract,
            text=payload.text,
            top_n=payload.top_n,
        )

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        upload = form.get("file")
        title = _get_optional_text(form.get("title"))
        abstract = _get_optional_text(form.get("abstract"))
        text = _get_optional_text(form.get("text"))
        top_n = _parse_top_n(form.get("top_n"))

        if _is_upload_file(upload):
            return await analysis_service.analyze_upload(
                upload=upload,
                title=title,
                abstract=abstract,
                text=text,
                top_n=top_n,
            )

        return analysis_service.analyze_text(
            title=title,
            abstract=abstract,
            text=text,
            top_n=top_n,
        )

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Use application/json, multipart/form-data, or application/x-www-form-urlencoded.",
    )


def _parse_top_n(value: str | None) -> int:
    if value is None or str(value).strip() == "":
        return settings.default_top_n
    try:
        parsed = int(str(value))
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="top_n must be an integer.",
        ) from error
    if not 1 <= parsed <= settings.max_top_n:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"top_n must be between 1 and {settings.max_top_n}.",
        )
    return parsed


def _get_optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _is_upload_file(value: object) -> bool:
    return isinstance(value, (UploadFile, StarletteUploadFile))
