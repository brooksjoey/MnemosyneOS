from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings

from mnemo.api.models import MemoryRecord
from mnemo.config.settings import settings
from mnemo.errors import VectorStoreUnavailable
from mnemo.vectorstores.base import BaseVectorStore


def _to_chroma_filter(filters: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """
    Convert simple filters into Chroma where-clause.
    Supports:
      - equality: {"category": "project"} or {"metadata.key": "value"}
      - contains: {"metadata.tags": {"$contains": "ai"}}
    """
    if not filters:
        return None

    where: Dict[str, Any] = {}
    for key, val in filters.items():
        if isinstance(val, dict) and "$contains" in val:
            # In Chroma, arrays are stored in metadata; emulate contains by equality on lists if supported,
            # else we keep a convention that 'tags' is a list and we compare directly with $contains hint.
            where[key] = {"$contains": val["$contains"]}
        else:
            where[key] = {"$eq": val}
    return where


class ChromaVectorStore(BaseVectorStore):
    """
    Chroma-backed vector store.

    Scoring: Chroma returns distances; for cosine, lower distance = closer.
    We convert to a similarity score = 1 - distance for client responses.
    """

    def __init__(self, dim: int):
        self._dim = dim
        try:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_DIR,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Failed to init Chroma: {e}") from e

    def _get_or_create(self, namespace: str):
        try:
            col = self._client.get_or_create_collection(
                name=namespace, metadata={"hnsw:space": "cosine"}
            )
            return col
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Chroma get_or_create_collection failed: {e}") from e

    def upsert(
        self,
        records: List[MemoryRecord],
        embeddings: List[List[float]],
        namespace: str = "default",
    ) -> None:
        if len(records) != len(embeddings):
            raise VectorStoreUnavailable("records and embeddings length mismatch")
        col = self._get_or_create(namespace)
        try:
            ids = [r.id or str(uuid.uuid4()) for r in records]
            metadatas = []
            documents = []
            for r in records:
                payload = {
                    "category": r.category,
                    "metadata": r.metadata or {},
                    "created_at": r.created_at.isoformat(),
                }
                metadatas.append(payload)
                documents.append(r.content)

            col.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Chroma upsert failed: {e}") from e

    def query(
        self,
        query_embedding: List[float],
        top_k: int,
        namespace: str = "default",
        filters: Dict[str, Any] | None = None,
    ) -> List[Tuple[MemoryRecord, float]]:
        col = self._get_or_create(namespace)

        where = _to_chroma_filter(filters)
        try:
            res = col.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances", "ids"],
            )
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Chroma query failed: {e}") from e

        out: List[Tuple[MemoryRecord, float]] = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            sim = 1.0 - float(dist)  # cosine similarity approximation
            rec = MemoryRecord(
                id=_id,
                content=doc,
                metadata=meta.get("metadata") if isinstance(meta, dict) else None,
                category=(meta or {}).get("category") if isinstance(meta, dict) else None,
                created_at=((meta or {}).get("created_at")),
            )
            # created_at may be str from storage; Pydantic will coerce on response
            out.append((rec, sim))
        return out

    def count(self, namespace: str = "default") -> int:
        col = self._get_or_create(namespace)
        try:
            return col.count()
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Chroma count failed: {e}") from e

    def reset(self, namespace: str = "default") -> None:
        try:
            self._client.delete_collection(namespace)
            self._client.get_or_create_collection(name=namespace, metadata={"hnsw:space": "cosine"})
        except Exception as e:  # noqa
            raise VectorStoreUnavailable(f"Chroma reset failed: {e}") from e