"""
SQLite table definitions and row types.
Content types: photo, video, text. Status: active, deleted.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

ContentType = Literal["photo", "video", "text"]
ContentStatus = Literal["active", "deleted"]


@dataclass
class Admin:
    """Admin user (added by owner)."""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    added_at: datetime


@dataclass
class Content:
    """Saved content for reposting."""
    id: int
    content_type: ContentType
    file_id: Optional[str]  # Telegram file_id for photo/video
    text: Optional[str]
    caption: Optional[str]
    status: ContentStatus
    publishing_enabled: bool
    created_at: datetime
    created_by: int  # telegram_id of admin


@dataclass
class Schedule:
    """Posting time (e.g. 09:00, 14:00, 18:00)."""
    id: int
    time_str: str  # "HH:MM"
    enabled: bool
    created_at: datetime


@dataclass
class PostLog:
    """Log of each repost to target group."""
    id: int
    content_id: int
    group_id: int
    message_id: int
    posted_at: datetime


@dataclass
class Setting:
    """Key-value settings (target_group_id, posting_enabled, banner_file_id)."""
    id: int
    key: str
    value: str
    updated_at: datetime
