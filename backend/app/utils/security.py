import re
from fastapi import HTTPException, UploadFile, status
from app.core.config import get_settings


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(your|the)\s+(system|developer)\s+prompt",
    r"exfiltrate|credential|api[_\-\s]?key",
]


def sanitize_research_query(query: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", query).strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Research query cannot be empty.")
    return cleaned[:4000]


def prompt_injection_score(text: str) -> int:
    lowered = text.lower()
    return sum(1 for pattern in PROMPT_INJECTION_PATTERNS if re.search(pattern, lowered))


async def validate_pdf_upload(file: UploadFile) -> bytes:
    settings = get_settings()
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF uploads are supported.")
    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {settings.max_upload_mb} MB limit.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
    return data
