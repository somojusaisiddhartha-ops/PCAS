import logging

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.schemas import AnalysisResponse
from app.services.file_service import extract_text_from_upload
from app.services.nlp_service import NLPService
from app.services.similarity_service import SimilarityService

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, similarity_service: SimilarityService) -> None:
        self.settings = get_settings()
        self.nlp_service = NLPService()
        self.similarity_service = similarity_service

    async def analyze_upload(
        self,
        upload,
        title: str | None,
        abstract: str | None,
        text: str | None,
        top_n: int,
    ) -> AnalysisResponse:
        extracted_text = await extract_text_from_upload(upload)
        merged_text = "\n".join(part for part in [text, extracted_text] if part and part.strip())
        return self._analyze_text_input(
            title=title,
            abstract=abstract,
            text=merged_text,
            top_n=top_n,
        )

    def analyze_text(
        self,
        title: str | None,
        abstract: str | None,
        text: str | None,
        top_n: int,
    ) -> AnalysisResponse:
        return self._analyze_text_input(title=title, abstract=abstract, text=text, top_n=top_n)

    def _analyze_text_input(
        self,
        title: str | None,
        abstract: str | None,
        text: str | None,
        top_n: int,
    ) -> AnalysisResponse:
        combined_text = self.nlp_service.combine_project_text(title=title, abstract=abstract, text=text)
        if not combined_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide a file or non-empty text/title/abstract input.",
            )

        bounded_top_n = min(max(top_n, 1), self.settings.max_top_n)
        logger.info("Running project similarity analysis with top_n=%s.", bounded_top_n)

        try:
            return self.similarity_service.analyze(
                query_text=combined_text,
                top_n=bounded_top_n,
                preprocess_fn=self.nlp_service.preprocess,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
