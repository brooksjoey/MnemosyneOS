src/api/schemas.py
from pydantic import BaseModel, Field
from typing import Any, List

class RememberIn(BaseModel):
    source_id: str = Field(..., max_length=255)
    content: str
    metadata: dict = Field(default_factory=dict)

class MemoryOut(BaseModel):
    id: str
    content: str
    metadata: dict

class RecallOut(BaseModel):
    id: str
    content: str
    metadata: dict
    score: float

class ClusterIn(BaseModel):
    clusters: List[List[str]]

class BackupOut(BaseModel):
    path: str