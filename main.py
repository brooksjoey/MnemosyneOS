from __future__ import annotations

import logging
import sys
import uuid

import orjson
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from mnemo.api.errors import install_exception_handlers
from mnemo.api.models import StatsResponse
from mnemo.api.routes import memories as memories_routes
from mnemo.api.routes import search as search_routes
from mnemo.config.settings import settings
from mnemo.security import require_api_key, rate_limit_key
from mnemo.services.memory_service import build_default_service

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO if settings.ENV == "production" else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("mnemo.main")
if settings.ENV == "development" and not settings.API_KEY:
    logger.warning("DEV MODE: API_KEY is not set; authentication is bypassed.")

# ---------- App ----------
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    default_response_class=None,  # allow FastAPI default JSONResponse
)


# ---------- CORS (adjust as needed) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Request ID middleware ----------
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response

# ---------- Rate Limiting ----------
limiter = Limiter(key_func=lambda req: rate_limit_key(req))
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ---------- Error Handlers ----------
install_exception_handlers(app)

# ---------- Health ----------
@app.get("/healthz")
@limiter.limit(settings.RATE_LIMIT)
async def healthz():
    # Lightweight provider ping could go here; for now, report configuration
    return {"status": "ok", "embeddings_provider": settings.EMBEDDINGS_PROVIDER, "vector_backend": settings.VECTOR_BACKEND}

# ---------- Auth dependency applied at router level ----------
app.include_router(memories_routes.router, dependencies=[limiter.limit(settings.RATE_LIMIT),])
app.include_router(search_routes.router, dependencies=[limiter.limit(settings.RATE_LIMIT),])

# Enforce API key on *all* routes except /healthz and /docs
@app.middleware("http")
async def api_key_enforcer(request: Request, call_next):
    if request.url.path in {"/healthz", "/docs", "/openapi.json"}:
        return await call_next(request)
    try:
        # dependency-style check
        from mnemo.security import require_api_key as _check
        # Inspect header
        api_key = request.headers.get("x-api-key")
        if settings.ENV != "development" or settings.API_KEY:
            if not api_key or api_key != settings.API_KEY:
                from mnemo.errors import UnauthorizedError
                raise UnauthorizedError("Invalid or missing API key.")
    except Exception as exc:  # handled by global handlers
        from mnemo.errors import UnauthorizedError
        if isinstance(exc, UnauthorizedError):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"error": "UNAUTHORIZED"})
        raise
    return await call_next(request)

# ---------- Stats ----------
@app.get("/meta/stats", response_model=StatsResponse)
@limiter.limit(settings.RATE_LIMIT)
def stats():
    svc = build_default_service()
    s = svc.stats()
    return StatsResponse(**s)


def run():
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=(settings.ENV == "development"))


if __name__ == "__main__":
    run()