from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from uuid import uuid4

from mnemo.api.models import MemoryCreate, MemoryRecord, SearchRequest, SearchResponse, SearchResultItem
from mnemo.config.settings import settings
from mnemo.embeddings.openai_provider import OpenAIEmbeddings
from mnemo.vectorstores.chroma_store import ChromaVectorStore
from mnemo.vectorstores.base import BaseVectorStore
from mnemo.embeddings.base import BaseEmbeddings


class MemoryService:
    def __init__(self, embeddings: BaseEmbeddings, store: BaseVectorStore, namespace: str = "default"):
        self._emb = embeddings
        self._store = store
        self._ns = namespace

    def add_memory(self, req: MemoryCreate) -> MemoryRecord:
        created_at = datetime.now(timezone.utc)
        rec = MemoryRecord(
            id=str(uuid4()),
            content=req.content,
            metadata=req.metadata,
            category=req.category,
            created_at=created_at,
        )
        embs = self._emb.embed_texts([rec.content])
        self._store.upsert([rec], embs, namespace=self._ns)
        return rec

    def search(self, req: SearchRequest) -> SearchResponse:
        q_emb = self._emb.embed_texts([req.query])[0]
        pairs = self._store.query(q_emb, top_k=req.limit, namespace=self._ns, filters=_normalize_filters(req.filters))
        items: List[SearchResultItem] = []
        for rec, score in pairs:
            items.append(
                SearchResultItem(
                    id=rec.id,
                    content=rec.content,
                    metadata=rec.metadata,
                    category=rec.category,
                    score=float(score),
                )
            )
        return SearchResponse(items=items, count=len(items))

    def stats(self) -> Dict[str, Any]:
        return {
            "total": self._store.count(self._ns),
            "vector_backend": settings.VECTOR_BACKEND,
            "embeddings_provider": settings.EMBEDDINGS_PROVIDER,
        }


def build_default_service() -> MemoryService:
    # Provider selection (for now we ship OpenAI + Chroma)
    emb = OpenAIEmbeddings()
    store = ChromaVectorStore(dim=emb.dimensions)
    return MemoryService(embeddings=emb, store=store)


def _normalize_filters(filters: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not filters:
        return None
    out: Dict[str, Any] = {}
    for k, v in filters.items():
        # Normalize "category" to top-level, and metadata paths to "metadata.*"
        if k.startswith("metadata."):
            out[k] = v
        elif k in {"category"}:
            out[k] = v
        elif k == "metadata":
            # Flatten one level if dict
            if isinstance(v, dict):
                for kk, vv in v.items():
                    out[f"metadata.{kk}"] = vv
        else:
            out[k] = v
    return out