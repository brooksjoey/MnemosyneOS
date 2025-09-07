from __future__ import annotations

from fastapi import APIRouter, Depends

from mnemo.api.models import SearchRequest, SearchResponse
from mnemo.services.memory_service import build_default_service, MemoryService

router = APIRouter(prefix="/search", tags=["search"])


def _svc() -> MemoryService:
    return build_default_service()


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, svc: MemoryService = Depends(_svc)) -> SearchResponse:
    return svc.search(payload)
