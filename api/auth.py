#!/usr/bin/env python3
"""Authorize Telethon and create/replace the local session file.

Run from api/:
    source .venv/bin/activate
    python auth.py

Stop the API first so it does not lock tg_session.session.
"""

from __future__ import annotations

import asyncio
import sys

from telethon import TelegramClient

from app.config import get_settings, session_path


async def main() -> None:
    settings = get_settings()
    if not settings.tg_api_id or not settings.tg_api_hash:
        print("Error: TG_API_ID and TG_API_HASH must be set in .env")
        raise SystemExit(1)

    path = session_path()
    session_file = path.with_suffix(".session")
    print(f"Session file: {session_file}")
    print("Log in with the NEW account (phone + code, then 2FA if enabled).\n")

    client = TelegramClient(str(path), settings.tg_api_id, settings.tg_api_hash)
    await client.start()
    me = await client.get_me()
    await client.disconnect()

    print("\nSuccess!")
    print(f"  name: {(me.first_name or '')} {(me.last_name or '')}".rstrip())
    print(f"  username: @{me.username}" if me.username else "  username: (none)")
    print(f"  id: {me.id}")
    print(f"  session: {session_file}")
    print("\nRestart the API, then POST /sync (or use Update feed).")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)
