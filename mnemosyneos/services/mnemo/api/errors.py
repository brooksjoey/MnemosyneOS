from __future__ import annotations

import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from mnemo.errors import (
    EmbeddingProviderUnavailable,
    VectorStoreUnavailable,
    UnauthorizedError,
)

logger = logging.getLogger("mnemo.api.errors")


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UnauthorizedError)
    async def _unauth(_: Request, exc: UnauthorizedError):
        rid = _ensure_request_id(_)
        _log_exc("UNAUTHORIZED", rid, exc)
        return JSONResponse(status_code=401, content={"error": "UNAUTHORIZED", "request_id": rid})

    @app.exception_handler(EmbeddingProviderUnavailable)
    async def _embeddings(_: Request, exc: EmbeddingProviderUnavailable):
        rid = _ensure_request_id(_)
        _log_exc("EMBEDDINGS_UNAVAILABLE", rid, exc)
        return JSONResponse(
            status_code=503,
            content={"error": "EMBEDDINGS_UNAVAILABLE", "message": str(exc), "request_id": rid},
        )

    @app.exception_handler(VectorStoreUnavailable)
    async def _vstore(_: Request, exc: VectorStoreUnavailable):
        rid = _ensure_request_id(_)
        _log_exc("VECTORSTORE_UNAVAILABLE", rid, exc)
        return JSONResponse(
            status_code=503,
            content={"error": "VECTORSTORE_UNAVAILABLE", "message": str(exc), "request_id": rid},
        )

    @app.exception_handler(ValidationError)
    async def _validation(_: Request, exc: ValidationError):
        rid = _ensure_request_id(_)
        _log_exc("BAD_REQUEST", rid, exc)
        return JSONResponse(
            status_code=400,
            content={"error": "BAD_REQUEST", "message": exc.errors(), "request_id": rid},
        )

    @app.exception_handler(Exception)
    async def _catch_all(_: Request, exc: Exception):
        rid = _ensure_request_id(_)
        _log_exc("INTERNAL_ERROR", rid, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "Internal Server Error", "request_id": rid},
        )


def _ensure_request_id(req: Request) -> str:
    rid = req.headers.get("x-request-id") or str(uuid.uuid4())
    req.state.request_id = rid
    return rid


def _log_exc(code: str, rid: str, exc: Exception) -> None:
    logger.exception("error_code=%s request_id=%s %s", code, rid, exc)