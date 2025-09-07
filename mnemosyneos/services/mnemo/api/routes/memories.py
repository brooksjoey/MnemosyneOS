from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from mnemo.api.models import MemoryCreate, MemoryRecord
from mnemo.services.memory_service import build_default_service, MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])


def _svc() -> MemoryService:
    return build_default_service()


@router.post("", response_model=MemoryRecord)
def create_memory(payload: MemoryCreate, svc: MemoryService = Depends(_svc)) -> MemoryRecord:
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="content must be non-empty")
    return svc.add_memory(payload)
