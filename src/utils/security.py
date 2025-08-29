<<<<<<< HEAD
from fastapi import Header, HTTPException, status, Request, Depends
from .settings import settings
import secrets
from typing import Annotated

def require_api_key(authorization: Annotated[str, Header()] = None):
    """
    Validates the provided API key against the configured keys.
    Raises a 403 if the default key is detected in a non-dev environment.
    """
    # Check for key presence
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header with Bearer token"
        )
    
    provided_key = authorization.split(" ", 1)[1]
    
    # THE MOST IMPORTANT CHECK: REJECT THE DEFAULT KEY
    if provided_key == "dev-key-123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The default API key is not allowed. Please set a secure API_KEYS environment variable."
        )
    
    # Check if key is valid
    if provided_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

# Optional: Better to use a Dependency for endpoint injection
def get_api_key(authorization: Annotated[str, Header()] = None) -> str:
    """Dependency to extract and validate API key, returning it for potential logging."""
    require_api_key(authorization) # Reuse the logic above
    return authorization.split(" ", 1)[1]

# You can now use `Depends(get_api_key)` in your route definitions
# and get the validated key string injected if you need to log it.

async def enforce_max_size(request: Request):
    # This is good. Keep it.
    cl = request.headers.get("content-length")
    if cl and int(cl) > settings.max_request_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")
=======
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
>>>>>>> bbeef0f (Initial commit with all project files)
