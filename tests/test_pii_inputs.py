tests/test_pii_inputs.py
from src.utils.redaction import redact

def test_redaction():
    t = "Call me at 555-555-5555 and email foo@bar.com"
    r = redact(t)
    assert "555" not in r and "@bar.com" not in r