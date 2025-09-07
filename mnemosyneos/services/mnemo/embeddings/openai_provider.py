from __future__ import annotations

import time
from typing import List

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APIError, RateLimitError, APITimeoutError

from mnemo.config.settings import settings
from mnemo.errors import EmbeddingProviderUnavailable
from mnemo.embeddings.base import BaseEmbeddings


_DEFAULT_MODEL = "text-embedding-3-small"
# As of OpenAI v1 SDK, typical dims: text-embedding-3-small = 1536
_MODEL_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class OpenAIEmbeddings(BaseEmbeddings):
    """OpenAI embeddings provider with retries, timeouts, and batching."""

    def __init__(self, model: str | None = None):
        if settings.OPENAI_API_KEY is None and settings.ENV == "production":
            raise EmbeddingProviderUnavailable("OPENAI_API_KEY must be set in production.")
        self._model = model or _DEFAULT_MODEL
        self._dims = _MODEL_DIMS.get(self._model, 1536)
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._timeout = float(settings.REQUEST_TIMEOUT_SECONDS)

    @property
    def dimensions(self) -> int:
        return self._dims

    def _chunk(self, texts: List[str], max_batch: int = 64) -> List[List[str]]:
        bucket: List[str] = []
        out: List[List[str]] = []
        for t in texts:
            bucket.append(t if isinstance(t, str) else str(t))
            if len(bucket) >= max_batch:
                out.append(bucket)
                bucket = []
        if bucket:
            out.append(bucket)
        return out

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError)),
        wait=wait_exponential(multiplier=0.5, min=1, max=8),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _embed_batch(self, batch: List[str]) -> List[List[float]]:
        try:
            resp = self._client.embeddings.create(
                model=self._model,
                input=batch,
                timeout=self._timeout,
            )
            return [d.embedding for d in resp.data]
        except (APIError, RateLimitError, APITimeoutError) as e:
            raise
        except Exception as e:  # noqa
            raise EmbeddingProviderUnavailable(f"Unexpected OpenAI error: {e}") from e

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            result: List[List[float]] = []
            for batch in self._chunk(texts, max_batch=64):
                embs = self._embed_batch(batch)
                result.extend(embs)
            # Sanity: ensure fixed length
            if any(len(v) != self._dims for v in result):
                raise EmbeddingProviderUnavailable(
                    f"Embedding dimension mismatch; expected {self._dims}."
                )
            return result
        except (APIError, RateLimitError, APITimeoutError) as e:
            raise EmbeddingProviderUnavailable(f"OpenAI rate-limited or unavailable: {e}")