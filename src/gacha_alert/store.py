from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import ReleaseItem


class SeenStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_items (
                    dedupe_key TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def filter_new(self, items: Iterable[ReleaseItem]) -> list[ReleaseItem]:
        new_items: list[ReleaseItem] = []
        with self._connect() as conn:
            for item in items:
                exists = conn.execute(
                    "SELECT 1 FROM seen_items WHERE dedupe_key = ?",
                    (item.dedupe_key,),
                ).fetchone()
                if exists is None:
                    new_items.append(item)
        return new_items

    def mark_seen(self, items: Iterable[ReleaseItem]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO seen_items (dedupe_key, source, item_id, title, url)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(item.dedupe_key, item.source, item.item_id, item.title, item.url) for item in items],
            )
