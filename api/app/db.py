from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_dir(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    parsed = make_url(url)
    if not parsed.database or parsed.database == ":memory:":
        return
    Path(parsed.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _resolve_sqlite_url(url: str) -> str:
    """Make relative sqlite paths absolute from api/ root."""
    if not url.startswith("sqlite:///"):
        return url
    rest = url.removeprefix("sqlite:///")
    if rest == ":memory:" or rest.startswith("/"):
        return url
    from app.config import API_ROOT

    return f"sqlite:///{(API_ROOT / rest).resolve()}"


def _make_engine():
    settings = get_settings()
    url = _resolve_sqlite_url(settings.database_url)
    _ensure_sqlite_dir(url)

    connect_args = {}
    if url.startswith("sqlite"):
        # Needed for FastAPI + SQLite across threads
        connect_args["check_same_thread"] = False

    engine = create_engine(url, connect_args=connect_args, future=True)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Import models so metadata is registered
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_posts_forward_columns()


def _migrate_sqlite_posts_forward_columns() -> None:
    """SQLite create_all does not ALTER existing tables — add forward cols if missing."""
    url = str(engine.url)
    if not url.startswith("sqlite"):
        return

    from sqlalchemy import text

    statements = [
        ("is_repost", "ALTER TABLE posts ADD COLUMN is_repost BOOLEAN NOT NULL DEFAULT 0"),
        ("forward_from_name", "ALTER TABLE posts ADD COLUMN forward_from_name VARCHAR(512)"),
        (
            "forward_from_username",
            "ALTER TABLE posts ADD COLUMN forward_from_username VARCHAR(255)",
        ),
        ("forward_from_tg_id", "ALTER TABLE posts ADD COLUMN forward_from_tg_id BIGINT"),
        (
            "forward_from_message_id",
            "ALTER TABLE posts ADD COLUMN forward_from_message_id BIGINT",
        ),
        ("forward_from_url", "ALTER TABLE posts ADD COLUMN forward_from_url VARCHAR(512)"),
        ("forward_date", "ALTER TABLE posts ADD COLUMN forward_date DATETIME"),
        (
            "forward_resolved",
            "ALTER TABLE posts ADD COLUMN forward_resolved BOOLEAN NOT NULL DEFAULT 0",
        ),
    ]

    with engine.begin() as conn:
        existing = {
            row[1] for row in conn.execute(text("PRAGMA table_info(posts)")).fetchall()
        }
        for col, ddl in statements:
            if col not in existing:
                conn.execute(text(ddl))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
