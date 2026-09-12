from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.ingest.telegram import run_sync
from app.schemas import SyncResponse

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
async def sync(db: Session = Depends(get_db)) -> SyncResponse:
    """On-demand ingest for all enabled channels."""
    return await run_sync(db)
