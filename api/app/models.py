from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Telegram peer id (optional until first successful sync)
    tg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    last_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    posts: Mapped[list["Post"]] = relationship(back_populates="channel")
    folder_links: Mapped[list["FolderChannel"]] = relationship(back_populates="channel")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("channel_id", "tg_message_id", name="uq_posts_channel_message"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tg_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Forward / repost (Telegram MessageFwdHeader)
    is_repost: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    forward_from_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    forward_from_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forward_from_tg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    forward_from_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    forward_from_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    forward_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # True once we've inspected Telegram fwd_from for this row
    forward_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    channel: Mapped["Channel"] = relationship(back_populates="posts")


class Folder(Base):
    """Telegram dialog filter (chat folder), keyed by Telegram filter id."""

    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Telegram filter id
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    channel_links: Mapped[list["FolderChannel"]] = relationship(
        back_populates="folder",
        cascade="all, delete-orphan",
    )


class FolderChannel(Base):
    __tablename__ = "folder_channels"
    __table_args__ = (
        UniqueConstraint("folder_id", "channel_id", name="uq_folder_channel"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    folder: Mapped["Folder"] = relationship(back_populates="channel_links")
    channel: Mapped["Channel"] = relationship(back_populates="folder_links")
