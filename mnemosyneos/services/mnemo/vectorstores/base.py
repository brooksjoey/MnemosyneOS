from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from mnemo.api.models import MemoryRecord


class BaseVectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def upsert(
        self,
        records: List[MemoryRecord],
        embeddings: List[List[float]],
        namespace: str = "default",
    ) -> None:
        """Insert or update vectors + payloads."""

    @abstractmethod
    def query(
        self,
        query_embedding: List[float],
        top_k: int,
        namespace: str = "default",
        filters: Dict[str, Any] | None = None,
    ) -> List[Tuple[MemoryRecord, float]]:
        """
        Return a list of (record, score) pairs.
        Score is cosine similarity (higher is better) or distance (document which).
        """

    @abstractmethod
    def count(self, namespace: str = "default") -> int:
        """Return number of stored items."""

    @abstractmethod
    def reset(self, namespace: str = "default") -> None:
        """Drop/clear namespace content."""