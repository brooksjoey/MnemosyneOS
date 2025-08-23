src/api/routes_ops.py
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from .deps import auth_dep
from ..db.session import get_db
from .schemas import ClusterIn, BackupOut
from ..core.compress import compress_clusters
from ..core.reflect import run_reflection
from ..utils.snapshots import backup_now, restore
from ..utils.settings import settings
from pathlib import Path

router = APIRouter(prefix="", tags=["ops"])

@router.post("/compress", response_model=dict, dependencies=[Depends(auth_dep)])
async def post_compress(body: ClusterIn, db: Session = Depends(get_db)):
    await compress_clusters(db, body.clusters)
    return {"status": "ok"}

@router.post("/reflect", response_model=dict, dependencies=[Depends(auth_dep)])
async def post_reflect(db: Session = Depends(get_db)):
    await run_reflection(db)
    return {"status": "ok"}

@router.post("/backup", response_model=BackupOut, dependencies=[Depends(auth_dep)])
def post_backup(kind: str = Body(default="full")):
    path = backup_now(kind)
    return BackupOut(path=path)

@router.post("/restore", response_model=dict, dependencies=[Depends(auth_dep)])
def post_restore(path: str = Body(...)):
    p = Path(path).resolve()
    base = Path(settings.backup_dir).resolve()
    if not str(p).endswith(".enc") or base not in p.parents:
        raise HTTPException(status_code=400, detail="Invalid snapshot path")
    restore(str(p))
    return {"status": "ok", "path": str(p)}