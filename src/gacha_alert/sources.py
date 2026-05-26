from __future__ import annotations

from abc import ABC, abstractmethod
from html import unescape
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

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
        # Keep the polling path fast and reliable: first collect list-page items only.
        # Detail pages can be slow or intermittently return 500, and fetching every
        # historical item's detail before dedupe makes scheduled runs time out.
        return super().fetch(character=character, keyword=keyword)

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


class TakaraTomyArtsScraper(SourceScraper):
    source_name = "takaratomy_arts"
    base_url = "https://www.takaratomy-arts.co.jp"

    def search_url(self, keyword: str) -> str:
        params = (
            "site=HLQCWXGN&charset=UTF-8&group=arts&design=arts01&sort=date"
            f"&query={quote(keyword)}"
        )
        return f"https://search.takaratomy-arts.co.jp/search?{params}"

    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        soup = BeautifulSoup(html, "html.parser")
        items_by_key: dict[str, ReleaseItem] = {}
        for link in soup.select("a[href]"):
            href = self._unwrap_click_url(link.get("href", ""))
            if "item.html?n=" not in href:
                continue
            url = urljoin(self.base_url, href)
            item_id = parse_qs(urlparse(url).query).get("n", [""])[0]
            if not item_id:
                continue

            title = self._clean_title(link.get_text(" ", strip=True))
            if title.startswith("http") or "item.html?n=" in title:
                title = ""
            if not title:
                title = self._clean_title(link.find_next(string=True) or "")
            if title.startswith("http") or "item.html?n=" in title:
                title = ""
            image = link.select_one("img[src]")
            item = ReleaseItem(
                source=self.source_name,
                item_id=item_id,
                title=title or item_id,
                url=url,
                character=character,
                keyword=keyword,
                image_url=urljoin(self.base_url, image.get("src", "")) if image else None,
            )
            existing = items_by_key.get(item.dedupe_key)
            if existing is None or (existing.title == item_id and item.title != item_id):
                items_by_key[item.dedupe_key] = item
        return list(items_by_key.values())

    @staticmethod
    def _unwrap_click_url(href: str) -> str:
        parsed = urlparse(href)
        if parsed.path.endswith("/click") or parsed.path == "/click":
            target = parse_qs(parsed.query).get("url", [""])[0]
            return unquote(target) if target else href
        return href

    @staticmethod
    def _clean_title(value: str) -> str:
        value = " ".join(value.split())
        return value.replace("｜商品情報｜タカラトミーアーツ", "").strip()


class QualiaScraper(SourceScraper):
    source_name = "qualia"
    base_url = "https://qualia-45.jp"
    products_url = "https://qualia-45.jp/products/"
    max_detail_pages = 80
    _detail_cache: dict[str, ReleaseItem] = {}

    def search_url(self, keyword: str) -> str:
        return self.products_url

    def fetch(self, character: str, keyword: str) -> list[ReleaseItem]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
            html = client.get(self.products_url, follow_redirects=True).raise_for_status().text
            urls = self._product_urls(html)
            items: list[ReleaseItem] = []
            for url in urls[: self.max_detail_pages]:
                item = self._detail_cache.get(url)
                if item is None:
                    detail_html = client.get(url, follow_redirects=True).raise_for_status().text
                    item = self.parse_detail(detail_html, url=url, character=character, keyword=keyword)
                    self._detail_cache[url] = item
                item = ReleaseItem(
                    source=item.source,
                    item_id=item.item_id,
                    title=item.title,
                    url=item.url,
                    character=character,
                    keyword=keyword,
                    image_url=item.image_url,
                    price=item.price,
                    release_text=item.release_text,
                    status_text=item.status_text,
                    description=item.description,
                    lineup_names=item.lineup_names,
                )
                haystack = " ".join(
                    [item.title, item.description or "", " ".join(item.lineup_names)]
                ).casefold()
                if keyword.casefold() in haystack:
                    items.append(item)
            return items

    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        return [
            ReleaseItem(
                source=self.source_name,
                item_id=urlparse(url).path.rstrip("/").split("/")[-1],
                title=urlparse(url).path.rstrip("/").split("/")[-1],
                url=url,
                character=character,
                keyword=keyword,
            )
            for url in self._product_urls(html)
        ]

    def parse_detail(self, html: str, url: str, character: str, keyword: str) -> ReleaseItem:
        soup = BeautifulSoup(html, "html.parser")
        title = self._first_text(soup.select_one("h1, .entry-title, title"))
        if title.endswith(" | Qualia"):
            title = title.removesuffix(" | Qualia").strip()
        text = soup.get_text("\n", strip=True)
        release_text = self._line_value(text, "発売日")
        price = self._line_value(text, "価格")
        image = soup.select_one('meta[property="og:image"][content], .post_content img[src], img[src]')
        image_url = image.get("content") if image and image.has_attr("content") else None
        if image is not None and not image_url:
            image_url = image.get("src")
        lineup_names = self._lineup_names(soup)
        item_id = urlparse(url).path.rstrip("/").split("/")[-1]
        return ReleaseItem(
            source=self.source_name,
            item_id=item_id,
            title=title or item_id,
            url=url,
            character=character,
            keyword=keyword,
            image_url=urljoin(self.base_url, image_url) if image_url else None,
            price=price,
            release_text=release_text,
            description=text[:500] if text else None,
            lineup_names=lineup_names,
        )

    @classmethod
    def _product_urls(cls, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        for link in soup.select('a[href*="/distinations/"]'):
            url = urljoin(cls.base_url, link.get("href", ""))
            if url not in urls:
                urls.append(url)
        return urls

    @staticmethod
    def _first_text(node) -> str:
        return node.get_text(" ", strip=True) if node else ""

    @staticmethod
    def _line_value(text: str, label: str) -> str | None:
        for line in text.splitlines():
            if line.startswith(label):
                return line.split("：", 1)[-1].strip() if "：" in line else line.strip()
        return None

    @staticmethod
    def _lineup_names(soup: BeautifulSoup) -> list[str]:
        heading = soup.find(string=lambda value: bool(value and value.strip() == "Lineup"))
        if not heading:
            return []
        names: list[str] = []
        for sibling in heading.find_all_next(string=True, limit=20):
            value = sibling.strip()
            if value and value not in {"Lineup", "商品情報", "素材表示"} and value not in names:
                names.append(value)
        return names[:12]


class KenElephantScraper(SourceScraper):
    source_name = "ken_elephant"
    base_url = "https://kenelestore.jp"
    collection_url = "https://kenelestore.jp/collections/miniature__latest/products.json?limit=250"

    def search_url(self, keyword: str) -> str:
        return self.collection_url

    def fetch(self, character: str, keyword: str) -> list[ReleaseItem]:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": USER_AGENT}) as client:
            payload = client.get(self.collection_url, follow_redirects=True).raise_for_status().json()
        return self.parse_products(payload.get("products", []), character=character, keyword=keyword)

    def parse(self, html: str, character: str, keyword: str) -> list[ReleaseItem]:
        return self.parse_products(httpx.Response(200, text=html).json().get("products", []), character, keyword)

    def parse_products(
        self, products: list[dict], character: str, keyword: str
    ) -> list[ReleaseItem]:
        items: list[ReleaseItem] = []
        for product in products:
            title = unescape(str(product.get("title") or "")).strip()
            body_html = str(product.get("body_html") or product.get("description") or "")
            tags = " ".join(str(tag) for tag in product.get("tags", []))
            haystack = BeautifulSoup(" ".join([title, body_html, tags]), "html.parser").get_text(
                " ", strip=True
            )
            if keyword.casefold() not in haystack.casefold():
                continue
            handle = str(product.get("handle") or product.get("id") or "").strip()
            product_id = str(product.get("id") or handle)
            images = product.get("images") or []
            image_url = None
            if images:
                first_image = images[0]
                image_url = first_image.get("src") if isinstance(first_image, dict) else str(first_image)
            variants = product.get("variants") or []
            price = None
            status = None
            if variants:
                first_variant = variants[0]
                price_value = first_variant.get("price")
                price = f"¥{price_value}" if price_value else None
                status = "販売中" if first_variant.get("available") else "在庫なし/予約終了"
            items.append(
                ReleaseItem(
                    source=self.source_name,
                    item_id=product_id,
                    title=title or handle,
                    url=f"{self.base_url}/products/{handle}" if handle else self.base_url,
                    character=character,
                    keyword=keyword,
                    image_url=image_url,
                    price=price,
                    status_text=status,
                    description=BeautifulSoup(body_html, "html.parser").get_text(" ", strip=True)[:500]
                    or None,
                )
            )
        return items


SCRAPERS: dict[str, type[SourceScraper]] = {
    "gashapon": GashaponScraper,
    "ichiban_kuji": IchibanKujiScraper,
    "takaratomy_arts": TakaraTomyArtsScraper,
    "qualia": QualiaScraper,
    "ken_elephant": KenElephantScraper,
}
