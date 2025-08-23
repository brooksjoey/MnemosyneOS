src/api/routes_health.py
from fastapi import APIRouter, Response, HTTPException
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from ..utils.settings import settings
from ..db.session import SessionLocal
from sqlalchemy import text
import redis

router = APIRouter(prefix="", tags=["health"])

@router.get("/healthz")
def healthz():
    return {"ok": True}

@router.get("/readyz")
def readyz():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        redis.from_url(settings.redis_url).ping()
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)