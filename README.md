# lead-feed

Единая лента постов из Telegram-каналов: сервисный аккаунт читает каналы по запросу, складывает текст в локальную БД, веб показывает timeline с фильтрами по папкам.

## Что умеет

- **On-demand sync** — обновление только по кнопке *Update feed* (без cron)
- **Каналы с аккаунта** — импорт публичных/доступных broadcast-каналов; **архив пропускается**
- **Папки Telegram** — чипы *Все* / папки / *Без папок*
- **Репосты** — пометка источника форварда
- **New** — лейбл на постах, появившихся после последнего sync в сессии
- **Пагинация** — *Загрузить ещё* (cursor)
- Текст только из Telegram (без Telegraph / медиа)

## Архитектура

```text
┌─────────────────┐     POST /sync      ┌──────────────────┐
│  Next.js :3010 │ ──────────────────► │  FastAPI :8000   │
│  лента + UI     │ ◄──── GET /posts ── │  Telethon ingest │
└─────────────────┘                     └────────┬─────────┘
                                                 │
                                                 ▼
                                            SQLite
                                   (схема совместима с Postgres /
                                    будущим Supabase)
```

| Путь | Роль |
|------|------|
| `web/` | Next.js 16, React, Tailwind, своя мини–дизайн-система |
| `api/` | FastAPI + Telethon + SQLAlchemy |

## Требования

- Node.js 20+
- Python 3.11+
- Telegram API credentials: [my.telegram.org/apps](https://my.telegram.org/apps)

## Быстрый старт

### 1. API

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните в `.env`:

```env
TG_API_ID=...
TG_API_HASH=...
TG_SESSION=tg_session
SYNC_BACKFILL_LIMIT=5
```

Авторизация (один раз; API в этот момент лучше остановить):

```bash
python auth.py
```

Запуск:

```bash
uvicorn app.main:app --reload --port 8000
```

Документация API: http://127.0.0.1:8000/docs

### 2. Web

```bash
cd web
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm install
npm run dev                  # http://localhost:3010
```

Порт **3010**, чтобы не пересекаться с типичным `:3000`.

### 3. Первый импорт каналов

Пока API запущен:

```bash
curl -X POST http://127.0.0.1:8000/channels/import-from-account
```

Подтянет неархивные каналы и папки аккаунта. Дальше в UI — *Update feed*.

## Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Жив ли API |
| `POST` | `/sync` | Синк всех enabled-каналов |
| `POST` | `/channels/import-from-account` | Каналы + папки с аккаунта |
| `GET` | `/channels` | Список каналов в БД |
| `GET` | `/folders` | Папки Telegram |
| `GET` | `/posts?limit=&cursor=&folder=` | Лента (`folder`: `all` \| `none` \| id) |

## Модель данных (кратко)

- **channels** — источники
- **posts** — текст, ссылка, метаданные репоста
- **folders** / **folder_channels** — привязка к Dialog Filters

Первый sync по каналу берёт до `SYNC_BACKFILL_LIMIT` свежих текстовых постов; дальше — только новые (`last_message_id`).

## Безопасность

Не коммитьте:

- `api/.env`
- `*.session` / бэкапы сессий
- `api/data/*.db`

Сессия Telethon = доступ к аккаунту. Для продукта используется **сервисный** user-аккаунт (не Bot API): публичные каналы можно читать без подписки; приватные — только если аккаунт внутри.

## Дальше

- Переезд SQLite → Supabase (Postgres): тот же `DATABASE_URL`
- UI управления каналами
- Более тонкий контроль sync (по папке / выбранным каналам)

## Лицензия

Пока не задана — уточните при необходимости.
