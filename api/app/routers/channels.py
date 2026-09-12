from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.ingest.telegram import import_account_channels
from app.models import Channel
from app.schemas import ChannelCreate, ChannelRead, ImportChannelsResponse

router = APIRouter(prefix="/channels", tags=["channels"])


def _normalize_username(raw: str) -> str:
    name = raw.strip().lstrip("@")
    if name.startswith("https://t.me/"):
        name = name.removeprefix("https://t.me/")
    if name.startswith("t.me/"):
        name = name.removeprefix("t.me/")
    name = name.split("/")[0].split("?")[0]
    return name.lower()


@router.get("", response_model=list[ChannelRead])
def list_channels(db: Session = Depends(get_db)) -> list[Channel]:
    return list(db.scalars(select(Channel).order_by(Channel.username)).all())


@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
def create_channel(body: ChannelCreate, db: Session = Depends(get_db)) -> Channel:
    username = _normalize_username(body.username)
    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    existing = db.scalar(select(Channel).where(Channel.username == username))
    if existing:
        raise HTTPException(status_code=409, detail=f"channel @{username} already exists")

    channel = Channel(username=username, title=body.title or username, enabled=True)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.post("/import-from-account", response_model=ImportChannelsResponse)
async def import_from_account(db: Session = Depends(get_db)) -> ImportChannelsResponse:
    """Add all broadcast channels from the logged-in Telegram account."""
    try:
        return await import_account_channels(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
