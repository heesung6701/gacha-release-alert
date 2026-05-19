from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseItem:
    source: str
    item_id: str
    title: str
    url: str
    character: str
    keyword: str
    image_url: str | None = None
    price: str | None = None
    release_text: str | None = None
    status_text: str | None = None

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.item_id}"
