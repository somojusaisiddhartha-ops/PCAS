import io
from pathlib import Path

from docx import Document
from fastapi import HTTPException, UploadFile, status


SUPPORTED_EXTENSIONS = {".docx"}


async def extract_text_from_upload(upload: UploadFile) -> str:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a Word document (.docx) or use the project title or abstract fields.",
        )

    data = await upload.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if extension == ".docx":
        return _extract_text_from_docx(data)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type. Upload a Word document (.docx) or use the project title or abstract fields.",
    )


def _extract_text_from_docx(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
