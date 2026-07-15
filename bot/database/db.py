"""Database layer for bot settings and logging."""

import aiosqlite
from pathlib import Path

from bot.constants import RECENT_POSTS_LIMIT


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return aiosqlite.connect(self.db_path)

    async def init(self) -> None:
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS post_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    post_text TEXT NOT NULL,
                    model_used TEXT,
                    trigger_type TEXT NOT NULL,
                    channel_id TEXT
                );

                CREATE TABLE IF NOT EXISTS model_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    model_name TEXT NOT NULL,
                    success INTEGER NOT NULL DEFAULT 1,
                    error_message TEXT
                );
                """
            )
            await db.commit()

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        async with self.connect() as db:
            await db.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            await db.commit()

    async def get_bool_setting(self, key: str, default: bool = False) -> bool:
        value = await self.get_setting(key)
        if value is None:
            return default
        return value.lower() in ("1", "true", "yes", "on")

    async def set_bool_setting(self, key: str, value: bool) -> None:
        await self.set_setting(key, "true" if value else "false")

    async def log_post(
        self,
        post_text: str,
        model_used: str | None,
        trigger_type: str,
        channel_id: str | None,
    ) -> None:
        async with self.connect() as db:
            await db.execute(
                """
                INSERT INTO post_log (post_text, model_used, trigger_type, channel_id)
                VALUES (?, ?, ?, ?)
                """,
                (post_text, model_used, trigger_type, channel_id),
            )
            await db.commit()

    async def log_model_usage(
        self, model_name: str, success: bool, error_message: str | None = None
    ) -> None:
        async with self.connect() as db:
            await db.execute(
                """
                INSERT INTO model_usage (model_name, success, error_message)
                VALUES (?, ?, ?)
                """,
                (model_name, 1 if success else 0, error_message),
            )
            await db.commit()

    async def get_model_stats_today(self) -> list[dict]:
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT model_name,
                       COUNT(*) as total,
                       SUM(success) as successes
                FROM model_usage
                WHERE date(created_at) = date('now')
                GROUP BY model_name
                ORDER BY total DESC
                """
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_recent_posts(self, limit: int = RECENT_POSTS_LIMIT) -> list[dict]:
        async with self.connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT created_at, post_text, model_used, trigger_type
                FROM post_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
