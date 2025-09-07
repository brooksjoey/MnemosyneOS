from __future__ import annotations

from fastapi import Depends, Header
from starlette.requests import Request

from mnemo.config.settings import settings
from mnemo.errors import UnauthorizedError


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Require X-API-Key header unless running in development with no API_KEY set.
    """
    if settings.ENV == "development" and not settings.API_KEY:
        # Dev-mode bypass with prominent log handled in main.py
        return
    if not settings.API_KEY or x_api_key != settings.API_KEY:
        raise UnauthorizedError("Invalid or missing API key.")


def rate_limit_key(request: Request, x_api_key: str | None = None) -> str:
    """
    Prefer API key for rate limit bucketing; fall back to client IP.
    """
    key = request.headers.get("X-API-Key") or x_api_key
    if key:
        return f"key:{key}"
    # Fallback to remote address
    client = request.client.host if request.client else "unknown"
    return f"ip:{client}"