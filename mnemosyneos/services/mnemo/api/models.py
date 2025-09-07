from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MemoryCreate(BaseModel):
    content: str = Field(..., description="Raw text content to store.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary metadata.")
    category: Optional[str] = Field(default=None, description="Optional memory category.")
    timestamp: Optional[datetime] = Field(default=None, description="Optional event timestamp.")


class MemoryRecord(BaseModel):
    id: str = Field(..., description="Unique memory id.")
    content: str = Field(..., description="Raw text content.")
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    created_at: datetime = Field(..., description="Creation time (server).")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "0c5ab1b7-2b3f-4b79-bec1-0f9e2d2a7b52",
            "content": "Remember to rotate API keys quarterly.",
            "metadata": {"source": "policy", "tags": ["security"]},
            "category": "procedural",
            "created_at": "2025-09-06T12:00:00Z",
        }
    })


class SearchRequest(BaseModel):
    query: str = Field(..., description="User query text.")
    limit: int = Field(default=5, ge=1, le=100, description="Max results to return.")
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description='Metadata/category filters, e.g. {"category":"project","metadata.tags":{"$contains":"ai"}}',
    )


class SearchResultItem(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    score: float = Field(..., description="Similarity score (higher is better).")


class SearchResponse(BaseModel):
    items: List[SearchResultItem]
    count: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "items": [
                {
                    "id": "a1b2c3",
                    "content": "I am setting up MnemosyneOS on my VPS...",
                    "metadata": {"source": "system setup", "tags": ["ai", "vps", "setup"]},
                    "category": "project",
                    "score": 0.87
                }
            ],
            "count": 1
        }
    })


class StatsResponse(BaseModel):
    total: int
    vector_backend: str
    embeddings_provider: str