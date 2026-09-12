from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import FolderChannel, Post
from app.schemas import PostsPage

router = APIRouter(prefix="/posts", tags=["posts"])


def _encode_cursor(posted_at: datetime, post_id: int) -> str:
    return f"{posted_at.isoformat()}|{post_id}"


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        raw_dt, raw_id = cursor.rsplit("|", 1)
        return datetime.fromisoformat(raw_dt), int(raw_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


@router.get("", response_model=PostsPage)
def list_posts(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    channel_id: int | None = None,
    folder: str | None = Query(
        None,
        description="all | none | <telegram folder id>",
    ),
    db: Session = Depends(get_db),
) -> PostsPage:
    stmt = (
        select(Post)
        .options(joinedload(Post.channel))
        .order_by(Post.posted_at.desc(), Post.id.desc())
        .limit(limit + 1)
    )
    if channel_id is not None:
        stmt = stmt.where(Post.channel_id == channel_id)

    folder_key = (folder or "all").strip().lower()
    if folder_key not in ("", "all"):
        if folder_key == "none":
            in_any = select(FolderChannel.channel_id).distinct()
            stmt = stmt.where(Post.channel_id.not_in(in_any))
        else:
            try:
                folder_id = int(folder_key)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="folder must be 'all', 'none', or a folder id",
                ) from exc
            in_folder = select(FolderChannel.channel_id).where(
                FolderChannel.folder_id == folder_id
            )
            stmt = stmt.where(Post.channel_id.in_(in_folder))

    if cursor:
        posted_at, post_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Post.posted_at < posted_at,
                (Post.posted_at == posted_at) & (Post.id < post_id),
            )
        )

    rows = list(db.scalars(stmt).unique().all())
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = _encode_cursor(last.posted_at, last.id)

    return PostsPage(items=items, next_cursor=next_cursor)
