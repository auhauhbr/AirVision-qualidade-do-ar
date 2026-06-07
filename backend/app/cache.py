import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class SQLiteCache:
    def __init__(self, db_path: Path, ttl_minutes: int) -> None:
        self.db_path = db_path
        self.ttl = timedelta(minutes=ttl_minutes)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def get(self, cache_key: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT payload, created_at FROM api_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row:
            return None
        created_at = datetime.fromisoformat(row[1])
        if datetime.now(timezone.utc) - created_at > self.ttl:
            return None
        return json.loads(row[0])

    def set(self, cache_key: str, payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO api_cache(cache_key, payload, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key)
                DO UPDATE SET payload = excluded.payload, created_at = excluded.created_at
                """,
                (cache_key, json.dumps(payload), now),
            )
