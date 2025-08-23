src/api/deps.py
from fastapi import Depends, Request
from ..utils.security import require_api_key, enforce_max_size
from ..db.session import get_db
from sqlalchemy.orm import Session

def auth_dep(authorization: str = Depends(require_api_key)):
    return True

async def size_limit_dep(request: Request):
    await enforce_max_size(request)

# Usage in routes: db: Session = Depends(get_db)