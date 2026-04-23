import logging
from collections import Counter
from dataclasses import dataclass
from math import log, sqrt

from app.models.project import Project
from app.models.schemas import AnalysisMeta, AnalysisResponse, SimilarProject

logger = logging.getLogger(__name__)


@dataclass
class IndexedProject:
    title: str
    abstract: str
    domain: str
    year: int
    searchable_text: str


class SimilarityService:
    def __init__(self) -> None:
        self.projects: list[IndexedProject] = []
        self.matrix: list[list[float]] | None = None
        self.vocabulary: dict[str, int] = {}
        self.idf_vector: list[float] | None = None

    def build_index(self, projects: list[Project], preprocess_fn) -> None:
        self.projects = [
            IndexedProject(
                title=project.title,
                abstract=project.abstract,
                domain=project.domain,
                year=project.year,
                searchable_text=preprocess_fn(f"{project.title} {project.abstract}"),
            )
            for project in projects
        ]

        corpus = [project.searchable_text for project in self.projects]
        self.matrix, self.vocabulary, self.idf_vector = self._fit_transform(corpus)
        logger.info("Built similarity index for %s projects.", len(self.projects))

    def analyze(self, query_text: str, top_n: int, preprocess_fn) -> AnalysisResponse:
        if not self.projects or self.matrix is None or self.idf_vector is None:
            raise ValueError("Similarity index is not initialized.")

        processed_query = preprocess_fn(query_text)
        if not processed_query:
            raise ValueError("Input text could not be processed.")

        query_vector = self._transform(processed_query)
        similarities = self._cosine_similarity(query_vector, self.matrix)
        ranked_indices = sorted(
            range(len(similarities)),
            key=lambda index: similarities[index],
            reverse=True,
        )[:top_n]

        similar_projects = [
            SimilarProject(
                title=self.projects[index].title,
                similarity=round(float(similarities[index] * 100), 2),
                domain=self.projects[index].domain,
                year=self.projects[index].year,
            )
            for index in ranked_indices
        ]

        max_similarity = similar_projects[0].similarity if similar_projects else 0.0
        uniqueness_score = round(max(0.0, 100 - max_similarity), 2)
        risk_level = self._classify_risk(uniqueness_score)
        summary = self._build_summary(uniqueness_score, max_similarity, risk_level)

        return AnalysisResponse(
            uniqueness_score=uniqueness_score,
            risk_level=risk_level,
            summary=summary,
            similar_projects=similar_projects,
            analysis_meta=AnalysisMeta(
                max_similarity=round(max_similarity, 2),
                matched_projects=len(similar_projects),
                input_length=len(query_text.split()),
            ),
        )

    @staticmethod
    def _classify_risk(uniqueness_score: float) -> str:
        if uniqueness_score <= 40:
            return "High"
        if uniqueness_score <= 70:
            return "Medium"
        return "Low"

    @staticmethod
    def _build_summary(uniqueness_score: float, max_similarity: float, risk_level: str) -> str:
        if max_similarity > 70:
            return (
                f"Warning: your project strongly overlaps with an existing record "
                f"({max_similarity:.1f}% similarity). This indicates a {risk_level.lower()} duplication risk."
            )
        if risk_level == "Medium":
            return (
                f"Your project shows moderate uniqueness. The highest overlap is "
                f"{max_similarity:.1f}%, so refinement is recommended before submission."
            )
        return (
            f"Your project appears relatively unique. The highest overlap is "
            f"{max_similarity:.1f}% with existing records, resulting in a {uniqueness_score:.1f}% uniqueness score."
        )

    def _fit_transform(
        self, corpus: list[str]
    ) -> tuple[list[list[float]] | None, dict[str, int], list[float] | None]:
        if not corpus:
            return None, {}, None

        tokenized_docs = [document.split() for document in corpus]
        vocabulary = {
            token: index
            for index, token in enumerate(sorted({token for doc in tokenized_docs for token in doc}))
        }
        doc_count = len(tokenized_docs)
        doc_frequencies = [0.0] * len(vocabulary)

        for tokens in tokenized_docs:
            for token in set(tokens):
                doc_frequencies[vocabulary[token]] += 1

        idf_vector = [log((1 + doc_count) / (1 + frequency)) + 1 for frequency in doc_frequencies]

        matrix = [self._vectorize_tokens(tokens, vocabulary, idf_vector) for tokens in tokenized_docs]
        return matrix, vocabulary, idf_vector

    def _transform(self, processed_text: str) -> list[float]:
        tokens = processed_text.split()
        return self._vectorize_tokens(tokens, self.vocabulary, self.idf_vector)

    @staticmethod
    def _vectorize_tokens(
        tokens: list[str], vocabulary: dict[str, int], idf_vector: list[float] | None
    ) -> list[float]:
        vector = [0.0] * len(vocabulary)
        if not tokens or idf_vector is None or not vocabulary:
            return vector

        counts = Counter(token for token in tokens if token in vocabulary)
        total_terms = sum(counts.values())
        if total_terms == 0:
            return vector

        for token, count in counts.items():
            index = vocabulary[token]
            tf = count / total_terms
            vector[index] = tf * idf_vector[index]
        return vector

    @staticmethod
    def _cosine_similarity(query_vector: list[float], matrix: list[list[float]]) -> list[float]:
        query_norm = sqrt(sum(value * value for value in query_vector))
        if query_norm == 0:
            return [0.0] * len(matrix)

        similarities: list[float] = []
        for row in matrix:
            numerator = sum(left * right for left, right in zip(row, query_vector, strict=False))
            row_norm = sqrt(sum(value * value for value in row))
            denominator = row_norm * query_norm
            similarities.append((numerator / denominator) if denominator else 0.0)
        return similarities
