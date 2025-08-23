src/utils/redaction.py
import re

EMAIL = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
PHONE = re.compile(r"\+?\d[\d\-\s]{8,}\d")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

def redact(text: str) -> str:
    """Best-effort PII redaction for email/phone/SSN."""
    text = EMAIL.sub("[redacted@email]", text)
    text = PHONE.sub("[redacted:phone]", text)
    text = SSN.sub("[redacted:ssn]", text)
    return text