from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import parse_qs, quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .models import ReleaseItem

USER_AGENT = "Mozilla/5.0 (compatible; gacha-release-alert/0.1; +https://github.com/)"


class SourceScraper(ABC):
    source_name: str

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch(self, character: str, keyword: str) -> list[ReleaseItem]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
            html = client.get(self.search_url(keyword), follow_redirects=True).raise_for_status().text
        return self.parse(html, character=character, keyword=keyword)

    @abstractmethod
    def search_url(self, keyword: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        raise NotImplementedError


class GashaponScraper(SourceScraper):
    source_name = "gashapon"
    base_url = "https://gashapon.jp/products/"

    def search_url(self, keyword: str) -> str:
        return f"https://gashapon.jp/products/result.php?free={quote(keyword)}"

    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[ReleaseItem] = []
        for card in soup.select(".pg-result__list, .c-card__list"):
            link = card.select_one('a.c-card__link[href*="detail.php"]')
            name = card.select_one(".c-card__name")
            if link is None or name is None:
                continue

            href = link.get("href", "")
            url = urljoin(self.base_url, href)
            item_id = self._item_id_from_url(url)
            if not item_id:
                continue

            image = card.select_one(".c-card__thumb img")
            price = card.select_one(".c-card__price--main")
            title = name.get_text(" ", strip=True)
            if not title:
                continue

            items.append(
                ReleaseItem(
                    source=self.source_name,
                    item_id=item_id,
                    title=title,
                    url=url,
                    character=character,
                    keyword=keyword,
                    image_url=image.get("src") if image else None,
                    price=f"{price.get_text(strip=True)}円" if price else None,
                    release_text=None,
                )
            )
        return items

    @staticmethod
    def _item_id_from_url(url: str) -> str:
        parsed = urlparse(url)
        jan_code = parse_qs(parsed.query).get("jan_code", [""])[0]
        return jan_code or parsed.path.rstrip("/").split("/")[-1]


class IchibanKujiScraper(SourceScraper):
    source_name = "ichiban_kuji"
    base_url = "https://1kuji.com"

    def search_url(self, keyword: str) -> str:
        return f"https://1kuji.com/search?word={quote(keyword)}"

    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[ReleaseItem] = []
        for card in soup.select("ul.itemList li"):
            link = card.select_one('a[href^="/products/"]')
            name = card.select_one(".itemName")
            if link is None or name is None:
                continue

            href = link.get("href", "")
            url = urljoin(self.base_url, href)
            item_id = href.rstrip("/").split("/")[-1]
            title = name.get_text(" ", strip=True)
            if not item_id or not title:
                continue

            image = card.select_one("img")
            statuses = [node.get_text(" ", strip=True) for node in card.select(".status")]
            dates = [node.get_text(" ", strip=True) for node in card.select(".date")]
            dates = [date for date in dates if date]

            items.append(
                ReleaseItem(
                    source=self.source_name,
                    item_id=item_id,
                    title=title,
                    url=url,
                    character=character,
                    keyword=keyword,
                    image_url=image.get("src") if image else None,
                    release_text=" / ".join(dates) or None,
                    status_text=" / ".join(statuses) or None,
                )
            )
        return items


SCRAPERS: dict[str, type[SourceScraper]] = {
    "gashapon": GashaponScraper,
    "ichiban_kuji": IchibanKujiScraper,
}
