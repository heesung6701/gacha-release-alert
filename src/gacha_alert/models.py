from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ReleaseItem:
    source: str
    item_id: str
    title: str
    url: str
    character: str
    keyword: str
    image_url: Optional[str] = None
    price: Optional[str] = None
    release_text: Optional[str] = None
    status_text: Optional[str] = None
    description: Optional[str] = None
    lineup_names: List[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.item_id}"


@dataclass(frozen=True)
class GashaponDetail:
    title: Optional[str] = None
    description: Optional[str] = None
    release_text: Optional[str] = None
    price: Optional[str] = None
    kind_count: Optional[str] = None
    target_age: Optional[str] = None
    lineup_names: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)
