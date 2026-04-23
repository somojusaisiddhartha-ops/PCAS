from app.utils.text import normalize_text


class NLPService:
    @staticmethod
    def combine_project_text(title: str | None, abstract: str | None, text: str | None) -> str:
        parts = [part.strip() for part in [title, abstract, text] if part and part.strip()]
        return "\n".join(parts)

    @staticmethod
    def preprocess(text: str) -> str:
        return normalize_text(text)
