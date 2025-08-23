src/llm/policy.py
from dataclasses import dataclass

@dataclass
class SourceTrust:
    domain: str
    weight: float

DEFAULT_TRUST = {"email": 0.6, "calendar": 0.7, "manual": 0.5, "system": 0.8}

def hybrid_score(vector_score: float, text_score: float) -> float:
    v = min(max(vector_score, 0.0), 1.0)
    t = min(max(text_score, 0.0), 1.0)
    return 0.65 * v + 0.35 * t