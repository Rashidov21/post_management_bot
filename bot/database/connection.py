"""
Async SQLite connection and database initialization.
"""
import aiosqlite
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

from config import DATABASE_PATH

logger = logging.getLogger(__name__)

# Singleton connection for app lifetime (SQLite works well with one conn per process)
_conn: Optional[aiosqlite.Connection] = None


async def get_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield a connection for request-scoped use."""
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn


def get_db() -> aiosqlite.Connection:
    """Return the app-level DB connection. Call after init_db()."""
    global _conn
    if _conn is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _conn


async def init_db() -> None:
    """Create tables if they do not exist (migration-less init)."""
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL CHECK(content_type IN ('photo', 'video', 'text')),
                file_id TEXT,
                text TEXT,
                caption TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'deleted')),
                publishing_enabled INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_str TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS content_schedule (
                schedule_id INTEGER PRIMARY KEY,
                content_id INTEGER NOT NULL,
                FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
                FOREIGN KEY (content_id) REFERENCES content(id)
            );

            CREATE TABLE IF NOT EXISTS posts_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (content_id) REFERENCES content(id)
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                source_content_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'taken')),
                taken_by_telegram_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered INTEGER NOT NULL DEFAULT 0,
                answered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (source_content_id) REFERENCES content(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_content_status ON content(status);
            CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
            CREATE INDEX IF NOT EXISTS idx_posts_log_content ON posts_log(content_id);
        """)
        await conn.commit()
        for sql in (
            "ALTER TABLE leads ADD COLUMN phone_number TEXT",
            "ALTER TABLE leads ADD COLUMN answered INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE leads ADD COLUMN answered_at TIMESTAMP",
            "ALTER TABLE content ADD COLUMN publishing_enabled INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE admins ADD COLUMN first_name TEXT",
            "ALTER TABLE admins ADD COLUMN last_name TEXT",
        ):
            try:
                await conn.execute(sql)
                await conn.commit()
            except Exception:
                pass
        try:
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status_answered ON leads(status, answered)")
            await conn.commit()
        except Exception:
            pass
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS content_schedule (
                    schedule_id INTEGER PRIMARY KEY,
                    content_id INTEGER NOT NULL,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
                    FOREIGN KEY (content_id) REFERENCES content(id)
                )
            """)
            await conn.commit()
        except Exception:
            pass
        logger.info("Database initialized: %s", DATABASE_PATH)


async def open_app_connection() -> aiosqlite.Connection:
    """Open and store the app-level connection. Call once at startup."""
    global _conn
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    _conn = await aiosqlite.connect(DATABASE_PATH)
    _conn.row_factory = aiosqlite.Row
    return _conn


async def close_app_connection() -> None:
    """Close the app-level connection. Call at shutdown."""
    global _conn
    if _conn:
        await _conn.close()
        _conn = None
        logger.info("Database connection closed.")
