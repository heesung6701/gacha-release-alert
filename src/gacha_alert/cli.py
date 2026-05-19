from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from .config import AppConfig, load_config
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
                items.extend(scraper.fetch(character=subscription.character, keyword=keyword))
    return _dedupe_in_memory(items)


def _dedupe_in_memory(items: Iterable[ReleaseItem]) -> list[ReleaseItem]:
    seen: set[str] = set()
    unique: list[ReleaseItem] = []
    for item in items:
        if item.dedupe_key in seen:
            continue
        seen.add(item.dedupe_key)
        unique.append(item)
    return unique


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

    notifier = DiscordNotifier(config.webhook_url_str, timeout_seconds=config.request_timeout_seconds)
    sent: list[ReleaseItem] = []
    for item in new_items:
        notifier.send(item)
        sent.append(item)

    store.mark_seen(sent)
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args.config, dry_run=args.dry_run, mark_seen_on_dry_run=args.mark_seen_on_dry_run)
    except Exception as exc:  # noqa: BLE001 - CLI should show a concise failure
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
