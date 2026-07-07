import re

from app.config import settings


def sanitize_input(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\s\.\,\?\!\-\:\;\"\'()]", "", text)
    return text[:10000]


def mask_pii(text: str) -> str:
    if not settings.PII_MASKING_ENABLED:
        return text

    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    text = re.sub(email_pattern, "[EMAIL]", text)

    phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    text = re.sub(phone_pattern, "[PHONE]", text)

    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    text = re.sub(ssn_pattern, "[SSN]", text)

    return text
