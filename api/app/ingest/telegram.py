"""Telegram ingest via Telethon (text only, no Telegraph)."""

from __future__ import annotations

import asyncio
from datetime import timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import Channel as TgChannel
from telethon.tl.types import DialogFilter

from app.config import get_settings, session_path
from app.models import Channel, Folder, FolderChannel, Post
from app.schemas import ImportChannelsResponse, SyncChannelResult, SyncResponse

_sync_lock = asyncio.Lock()


def _message_text(msg) -> str:
    # Prefer .text (includes caption); fall back to .message
    raw = msg.text or getattr(msg, "message", None) or ""
    return raw.replace("\r\n", "\n").replace("\r", "\n").strip()


def _post_url(username: str | None, message_id: int) -> str | None:
    if not username or username.startswith("id:"):
        return None
    return f"https://t.me/{username}/{message_id}"


def _channel_key(entity: TgChannel) -> str:
    if entity.username:
        return entity.username.lower()
    return f"id:{entity.id}"


async def _forward_meta(client: TelegramClient, msg) -> dict:
    """Extract Telegram forward/repost fields from a message."""
    fwd = getattr(msg, "fwd_from", None)
    if not fwd:
        return {
            "is_repost": False,
            "forward_from_name": None,
            "forward_from_username": None,
            "forward_from_tg_id": None,
            "forward_from_message_id": None,
            "forward_from_url": None,
            "forward_date": None,
        }

    name = getattr(fwd, "from_name", None) or getattr(fwd, "post_author", None)
    username: str | None = None
    tg_id: int | None = None
    message_id = getattr(fwd, "channel_post", None)
    url: str | None = None

    from_id = getattr(fwd, "from_id", None)
    if from_id is not None:
        try:
            src = await client.get_entity(from_id)
            tg_id = int(getattr(src, "id", 0) or 0) or None
            username = getattr(src, "username", None)
            if username:
                username = username.lower()
            title = getattr(src, "title", None) or getattr(src, "first_name", None)
            if title:
                name = title
            if username and message_id:
                url = _post_url(username, int(message_id))
        except Exception:  # noqa: BLE001
            pass

    forward_date = getattr(fwd, "date", None)
    if forward_date is not None and forward_date.tzinfo is None:
        forward_date = forward_date.replace(tzinfo=timezone.utc)

    return {
        "is_repost": True,
        "forward_from_name": name,
        "forward_from_username": username,
        "forward_from_tg_id": tg_id,
        "forward_from_message_id": int(message_id) if message_id else None,
        "forward_from_url": url,
        "forward_date": forward_date,
    }


def _apply_forward_fields(post: Post, meta: dict) -> None:
    post.is_repost = bool(meta["is_repost"])
    post.forward_from_name = meta["forward_from_name"]
    post.forward_from_username = meta["forward_from_username"]
    post.forward_from_tg_id = meta["forward_from_tg_id"]
    post.forward_from_message_id = meta["forward_from_message_id"]
    post.forward_from_url = meta["forward_from_url"]
    post.forward_date = meta["forward_date"]
    post.forward_resolved = True


async def _resolve_entity(client: TelegramClient, channel: Channel):
    if channel.tg_id is not None:
        try:
            return await client.get_entity(channel.tg_id)
        except (ValueError, UsernameInvalidError, UsernameNotOccupiedError):
            pass
    return await client.get_entity(channel.username)


async def _backfill_forward_meta(
    client: TelegramClient,
    db: Session,
    channel: Channel,
    entity,
) -> int:
    """Refresh forward metadata for posts not yet inspected."""
    posts = list(
        db.scalars(
            select(Post).where(
                Post.channel_id == channel.id,
                Post.forward_resolved.is_(False),
            )
        ).all()
    )
    if not posts:
        return 0

    by_tg_id = {p.tg_message_id: p for p in posts}
    async for msg in client.iter_messages(entity, ids=list(by_tg_id.keys())):
        if msg is None or msg.id is None:
            continue
        post = by_tg_id.get(msg.id)
        if post is None:
            continue
        meta = await _forward_meta(client, msg)
        _apply_forward_fields(post, meta)
    db.commit()
    return len(posts)


async def _sync_channel(
    client: TelegramClient,
    db: Session,
    channel: Channel,
    *,
    backfill_limit: int,
) -> SyncChannelResult:
    try:
        entity = await _resolve_entity(client, channel)
    except (UsernameInvalidError, UsernameNotOccupiedError, ValueError) as exc:
        return SyncChannelResult(username=channel.username, added=0, error=str(exc))

    title = getattr(entity, "title", None) or channel.title or channel.username
    peer_username = getattr(entity, "username", None)
    tg_id = getattr(entity, "id", None)

    channel.title = title
    if tg_id is not None:
        channel.tg_id = int(tg_id)
    if peer_username:
        channel.username = peer_username.lower()

    min_id = channel.last_message_id
    kwargs: dict = {}
    if min_id:
        kwargs["min_id"] = int(min_id)
    else:
        kwargs["limit"] = backfill_limit

    added = 0
    max_seen_id = int(min_id or 0)

    try:
        async for msg in client.iter_messages(entity, **kwargs):
            if msg.id is None:
                continue
            if msg.id > max_seen_id:
                max_seen_id = msg.id

            text = _message_text(msg)
            if not text:
                continue

            existing = db.scalar(
                select(Post).where(
                    Post.channel_id == channel.id,
                    Post.tg_message_id == msg.id,
                )
            )
            meta = await _forward_meta(client, msg)
            if existing:
                _apply_forward_fields(existing, meta)
                continue

            posted_at = msg.date
            if posted_at is not None and posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)

            post = Post(
                channel_id=channel.id,
                tg_message_id=msg.id,
                posted_at=posted_at,
                text=text,
                url=_post_url(peer_username, msg.id),
            )
            _apply_forward_fields(post, meta)
            db.add(post)
            added += 1

        # One-shot style refresh for rows already in DB (e.g. before forward fields existed)
        await _backfill_forward_meta(client, db, channel, entity)

    except FloodWaitError as exc:
        db.rollback()
        await asyncio.sleep(exc.seconds)
        return SyncChannelResult(
            username=channel.username,
            added=0,
            error=f"FloodWait {exc.seconds}s — retry later",
        )

    if max_seen_id > 0:
        channel.last_message_id = max_seen_id

    db.commit()
    return SyncChannelResult(username=channel.username, added=added, error=None)


async def _telegram_client() -> TelegramClient:
    settings = get_settings()
    if not settings.tg_api_id or not settings.tg_api_hash:
        raise RuntimeError("TG_API_ID and TG_API_HASH must be set in api/.env")

    path = session_path()
    if not path.with_suffix(".session").exists():
        raise RuntimeError(f"Session file not found: {path.with_suffix('.session')}")

    client = TelegramClient(str(path), settings.tg_api_id, settings.tg_api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError("Telethon session is not authorized — re-run auth")
    return client


def _is_archived_dialog(dialog) -> bool:
    """Telegram archive folder is folder_id == 1; Telethon also sets dialog.archived."""
    return bool(getattr(dialog, "archived", False)) or getattr(dialog, "folder_id", None) == 1


def _filter_title(raw) -> str:
    if hasattr(raw, "text"):
        return str(raw.text)
    return str(raw)


async def refresh_folders(client: TelegramClient, db: Session) -> int:
    """Replace folder rows from Telegram dialog filters (broadcast channels only)."""
    db.execute(delete(FolderChannel))
    db.execute(delete(Folder))
    db.flush()

    by_tg_id = {
        c.tg_id: c
        for c in db.scalars(select(Channel)).all()
        if c.tg_id is not None
    }

    result = await client(GetDialogFiltersRequest())
    filters = getattr(result, "filters", result)
    count = 0

    for f in filters:
        if not isinstance(f, DialogFilter):
            continue
        folder = Folder(id=int(f.id), title=_filter_title(f.title))
        db.add(folder)
        db.flush()
        count += 1

        peers = list(f.pinned_peers or []) + list(f.include_peers or [])
        seen_channels: set[int] = set()
        for peer in peers:
            try:
                entity = await client.get_entity(peer)
            except Exception:  # noqa: BLE001
                continue
            if not isinstance(entity, TgChannel) or not getattr(entity, "broadcast", False):
                continue
            channel = by_tg_id.get(int(entity.id))
            if channel is None or channel.id in seen_channels:
                continue
            seen_channels.add(channel.id)
            db.add(FolderChannel(folder_id=folder.id, channel_id=channel.id))

    db.commit()
    return count


async def import_account_channels(db: Session) -> ImportChannelsResponse:
    """Pull non-archived broadcast channels from the logged-in account into the DB."""
    client = await _telegram_client()
    added = 0
    existing = 0
    removed = 0
    imported: list[str] = []

    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if not isinstance(entity, TgChannel):
                continue
            # Broadcast channels only (skip groups / megagroups)
            if not getattr(entity, "broadcast", False):
                continue

            username = _channel_key(entity)
            title = getattr(entity, "title", None) or username
            tg_id = int(entity.id)

            row = db.scalar(
                select(Channel).where(
                    (Channel.tg_id == tg_id) | (Channel.username == username)
                )
            )

            # Archived channels must not stay in the DB
            if _is_archived_dialog(dialog):
                if row:
                    db.execute(delete(Post).where(Post.channel_id == row.id))
                    db.delete(row)
                    removed += 1
                continue

            if row:
                row.title = title
                row.tg_id = tg_id
                row.username = username
                row.enabled = True
                existing += 1
            else:
                db.add(
                    Channel(
                        username=username,
                        title=title,
                        tg_id=tg_id,
                        enabled=True,
                    )
                )
                added += 1
                imported.append(username)

        db.commit()
        await refresh_folders(client, db)
    finally:
        await client.disconnect()

    return ImportChannelsResponse(
        status="ok",
        message=(
            f"Imported {added} new channel(s), updated {existing} existing, "
            f"removed {removed} archived"
        ),
        added=added,
        existing=existing,
        removed=removed,
        channels=imported,
    )


async def run_sync(db: Session) -> SyncResponse:
    settings = get_settings()
    try:
        # Validate credentials early with a clear response
        _ = settings.tg_api_id, settings.tg_api_hash
        if not settings.tg_api_id or not settings.tg_api_hash:
            return SyncResponse(
                status="error",
                message="TG_API_ID and TG_API_HASH must be set in api/.env",
                added=0,
            )
        if not session_path().with_suffix(".session").exists():
            return SyncResponse(
                status="error",
                message=f"Session file not found: {session_path().with_suffix('.session')}",
                added=0,
            )
    except Exception as exc:  # noqa: BLE001
        return SyncResponse(status="error", message=str(exc), added=0)

    if _sync_lock.locked():
        return SyncResponse(
            status="busy",
            message="Sync already in progress",
            added=0,
        )

    async with _sync_lock:
        channels = list(
            db.scalars(
                select(Channel).where(Channel.enabled.is_(True)).order_by(Channel.username)
            ).all()
        )
        if not channels:
            return SyncResponse(
                status="ok",
                message="No enabled channels to sync",
                added=0,
            )

        results: list[SyncChannelResult] = []
        total_added = 0

        client = await _telegram_client()
        try:
            for index, channel in enumerate(channels):
                result = await _sync_channel(
                    client,
                    db,
                    channel,
                    backfill_limit=settings.sync_backfill_limit,
                )
                results.append(result)
                total_added += result.added
                if index < len(channels) - 1:
                    await asyncio.sleep(settings.sync_channel_pause_seconds)
        finally:
            await client.disconnect()

        errors = [r for r in results if r.error]
        status = "ok" if not errors else "partial"
        message = (
            f"Synced {len(results)} channel(s), added {total_added} post(s)"
            if not errors
            else f"Synced with {len(errors)} error(s), added {total_added} post(s)"
        )
        return SyncResponse(
            status=status,
            message=message,
            added=total_added,
            channels=results,
        )
