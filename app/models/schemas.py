from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeTextRequest(BaseModel):
    title: str | None = None
    abstract: str | None = None
    text: str | None = None
    top_n: int = Field(default=5, ge=1, le=10)


class SimilarProject(BaseModel):
    title: str
    similarity: float
    domain: str
    year: int


class AnalysisMeta(BaseModel):
    max_similarity: float
    matched_projects: int
    input_length: int


class AnalysisResponse(BaseModel):
    uniqueness_score: float
    risk_level: Literal["Low", "Medium", "High"]
    summary: str
    similar_projects: list[SimilarProject]
    analysis_meta: AnalysisMeta


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    abstract: str
    domain: str
    year: int
