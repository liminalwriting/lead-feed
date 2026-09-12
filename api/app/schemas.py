from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChannelCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    title: str | None = None


class ChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    title: str | None
    tg_id: int | None
    last_message_id: int | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    tg_message_id: int
    posted_at: datetime
    text: str
    url: str | None
    is_repost: bool = False
    forward_from_name: str | None = None
    forward_from_username: str | None = None
    forward_from_tg_id: int | None = None
    forward_from_message_id: int | None = None
    forward_from_url: str | None = None
    forward_date: datetime | None = None
    created_at: datetime
    channel: ChannelRead | None = None


class PostsPage(BaseModel):
    items: list[PostRead]
    next_cursor: str | None = None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str


class SyncChannelResult(BaseModel):
    username: str
    added: int = 0
    error: str | None = None


class SyncResponse(BaseModel):
    status: str
    message: str
    added: int = 0
    channels: list[SyncChannelResult] = Field(default_factory=list)


class ImportChannelsResponse(BaseModel):
    status: str
    message: str
    added: int = 0
    existing: int = 0
    removed: int = 0
    channels: list[str] = Field(default_factory=list)
