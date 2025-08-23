src/utils/security.py
from fastapi import Header, HTTPException, status, Request
from .settings import settings

def require_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token not in settings.api_keys:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

async def enforce_max_size(request: Request):
    cl = request.headers.get("content-length")
    if cl and int(cl) > settings.max_request_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")