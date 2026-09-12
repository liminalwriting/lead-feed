from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Folder
from app.schemas import FolderRead

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=list[FolderRead])
def list_folders(db: Session = Depends(get_db)) -> list[Folder]:
    return list(db.scalars(select(Folder).order_by(Folder.title)).all())
