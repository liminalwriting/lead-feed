# lead-feed

Personal feed: Telegram channels → SQLite → unified web timeline.

## Architecture

```text
web/   Next.js :3010   — feed UI, Sync button
api/   FastAPI :8000   — Telethon ingest (on demand)
       SQLite          — local DB (schema ready for Supabase later)
```

## Status

- [x] Step 1 — Next.js + Tailwind + tokens + feed stubs
- [x] Step 2 — FastAPI skeleton + SQLite schema
- [x] Step 3 — Telethon sync (session from telegram-parser)
- [x] Step 4 — Wire Sync button → API → refresh feed

## Dev

```bash
# api (terminal 1)
cd api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# web (terminal 2)
cd web
cp .env.example .env.local   # if needed
npm run dev
```

- Web: http://localhost:3010  
- API docs: http://127.0.0.1:8000/docs
