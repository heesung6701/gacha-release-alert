from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import AppConfig, load_config
from .korean import translated_release_dict
from .models import ReleaseItem
from .notifier import DiscordNotifier
from .sources import SCRAPERS
from .store import SeenStore


def collect_items(config: AppConfig) -> list[ReleaseItem]:
    items: list[ReleaseItem] = []
    for subscription in config.subscriptions:
        for keyword in subscription.keywords:
            for source in subscription.sources:
                scraper_cls = SCRAPERS[source]
                scraper = scraper_cls(timeout_seconds=config.request_timeout_seconds)
                try:
                    items.extend(scraper.fetch(character=subscription.character, keyword=keyword))
                except Exception as exc:  # noqa: BLE001 - keep other sources/keywords alive
                    print(
                        f"WARN: skipped source={source} character={subscription.character} keyword={keyword}: {exc}",
                        file=sys.stderr,
                    )
    return _dedupe_in_memory(items)


def _dedupe_in_memory(items: Iterable[ReleaseItem]) -> list[ReleaseItem]:
    seen_ids: set[str] = set()
    seen_titles: set[tuple[str, str, str]] = set()
    unique: list[ReleaseItem] = []
    for item in items:
        title_key = (item.source, item.character, _normalize_title(item.title))
        if item.dedupe_key in seen_ids or title_key in seen_titles:
            continue
        seen_ids.add(item.dedupe_key)
        seen_titles.add(title_key)
        unique.append(item)
    return unique


def _normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())


def run(config_path: str, dry_run: bool = False, mark_seen_on_dry_run: bool = False) -> int:
    config = load_config(config_path)
    store = SeenStore(config.database_path)
    items = collect_items(config)
    new_items = store.filter_new(items)

    print(f"fetched={len(items)} new={len(new_items)}")
    for item in new_items:
        print(f"- [{item.source}] {item.title} | {item.url}")

    if dry_run:
        if mark_seen_on_dry_run:
            store.mark_seen(new_items)
        return 0

    notifier = DiscordNotifier(
        config.webhook_url_str,
        timeout_seconds=config.request_timeout_seconds,
        webhook_secret=config.webhook_secret_str,
    )
    sent: list[ReleaseItem] = []
    for item in new_items:
        notifier.send(item)
        sent.append(item)

    store.mark_seen(sent)
    return 0


def export_json(config_path: str, output_path: str) -> int:
    config = load_config(config_path)
    items = collect_items(config)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": [translated_release_dict(asdict(item)) for item in items],
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"exported={len(items)} path={output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bandai Gashapon / Ichiban Kuji release alerts")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Print new items without sending Discord")
    parser.add_argument(
        "--mark-seen-on-dry-run",
        action="store_true",
        help="When used with --dry-run, record printed items as seen",
    )
    parser.add_argument(
        "--export-json",
        metavar="PATH",
        help="Fetch current release items and write a static JSON file for GitHub Pages",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.export_json:
            return export_json(args.config, args.export_json)
        return run(args.config, dry_run=args.dry_run, mark_seen_on_dry_run=args.mark_seen_on_dry_run)
    except Exception as exc:  # noqa: BLE001 - CLI should show a concise failure
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
