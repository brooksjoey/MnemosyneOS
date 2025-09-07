from __future__ import annotations


class EmbeddingProviderUnavailable(RuntimeError):
    """Raised when the embeddings provider is unavailable or failing persistently."""


class VectorStoreUnavailable(RuntimeError):
    """Raised when the vector store is unavailable or misconfigured."""


class UnauthorizedError(RuntimeError):
    """Raised when the request lacks a valid API key."""