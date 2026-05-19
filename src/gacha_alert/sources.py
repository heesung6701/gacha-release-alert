from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import parse_qs, quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .models import GashaponDetail, ReleaseItem

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

    def fetch(self, character: str, keyword: str) -> list[ReleaseItem]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
            html = client.get(self.search_url(keyword), follow_redirects=True).raise_for_status().text
            items = self.parse(html, character=character, keyword=keyword)
            enriched_items: list[ReleaseItem] = []
            for item in items:
                detail_html = client.get(item.url, follow_redirects=True).raise_for_status().text
                enriched_items.append(self.enrich_item(item, self.parse_detail(detail_html)))
        return enriched_items

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

    def parse_detail(self, html: str) -> GashaponDetail:
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one(".pg-heading")
        description_node = soup.select_one(".pg-detail__description")
        definitions = self._parse_detail_definitions(soup)

        image_urls: list[str] = []
        lineup_names: list[str] = []
        for image in soup.select('.pg-detail__picture img[src]'):
            image_url = image.get("src", "").strip()
            if image_url and image_url not in image_urls:
                image_urls.append(image_url)
            lineup_name = image.get("title", "").strip() or image.get("alt", "").strip()
            if lineup_name and lineup_name not in lineup_names:
                lineup_names.append(lineup_name)

        return GashaponDetail(
            title=title_node.get_text(" ", strip=True) if title_node else None,
            description=description_node.get_text(" ", strip=True) if description_node else None,
            release_text=definitions.get("発売時期"),
            price=definitions.get("価格(税込)") or definitions.get("価格"),
            kind_count=definitions.get("種類数"),
            target_age=definitions.get("対象年齢"),
            lineup_names=lineup_names,
            image_urls=image_urls,
        )

    def enrich_item(self, item: ReleaseItem, detail: GashaponDetail) -> ReleaseItem:
        status_parts = [part for part in [detail.kind_count, detail.target_age] if part]
        return ReleaseItem(
            source=item.source,
            item_id=item.item_id,
            title=detail.title or item.title,
            url=item.url,
            character=item.character,
            keyword=item.keyword,
            image_url=detail.image_urls[0] if detail.image_urls else item.image_url,
            price=detail.price or item.price,
            release_text=detail.release_text or item.release_text,
            status_text=" / ".join(status_parts) or item.status_text,
            description=detail.description or item.description,
            lineup_names=detail.lineup_names or item.lineup_names,
        )

    @staticmethod
    def _parse_detail_definitions(soup: BeautifulSoup) -> dict[str, str]:
        definitions: dict[str, str] = {}
        for block in soup.select(".pg-detailDefinition"):
            title = block.select_one(".pg-detailDefinition__title")
            detail = block.select_one(".pg-detailDefinition__detail")
            if title is None or detail is None:
                continue
            title_text = " ".join(title.get_text(" ", strip=True).split())
            detail_text = " ".join(detail.get_text(" ", strip=True).split())
            if title_text and detail_text:
                definitions[title_text] = detail_text
        return definitions

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
