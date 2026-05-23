import json

from gacha_alert import cli
from gacha_alert.models import ReleaseItem


def test_export_json_writes_static_pages_payload(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    output_path = tmp_path / "public" / "data" / "releases.json"
    config_path.write_text(
        """
discord_webhook_url: ""
database_path: "data/test.sqlite3"
subscriptions:
  - character: "짱구"
    keywords: ["クレヨンしんちゃん"]
    sources: ["gashapon"]
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli,
        "collect_items",
        lambda config: [
            ReleaseItem(
                source="gashapon",
                item_id="1",
                title="테스트 가챠",
                url="https://example.com/item/1",
                character="짱구",
                keyword="クレヨンしんちゃん",
                image_url="https://example.com/item/1.png",
            )
        ],
    )

    assert cli.export_json(str(config_path), str(output_path)) == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["generated_at"]
    assert payload["items"][0]["title"] == "테스트 가챠"
    assert payload["items"][0]["title_ko"] == "테스트 가챠"
    assert payload["items"][0]["character"] == "짱구"


def test_export_json_reuses_generated_at_when_items_are_unchanged(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    output_path = tmp_path / "public" / "data" / "releases.json"
    config_path.write_text(
        """
discord_webhook_url: ""
database_path: "data/test.sqlite3"
subscriptions:
  - character: "짱구"
    keywords: ["クレヨンしんちゃん"]
    sources: ["gashapon"]
""".strip(),
        encoding="utf-8",
    )

    item = ReleaseItem(
        source="gashapon",
        item_id="1",
        title="테스트 가챠",
        url="https://example.com/item/1",
        character="짱구",
        keyword="クレヨンしんちゃん",
    )
    monkeypatch.setattr(cli, "collect_items", lambda config: [item])

    assert cli.export_json(str(config_path), str(output_path)) == 0
    first_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli.export_json(str(config_path), str(output_path)) == 0
    second_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert second_payload["generated_at"] == first_payload["generated_at"]
    assert second_payload == first_payload


def test_dedupe_in_memory_collapses_same_source_character_title():
    items = [
        ReleaseItem(
            source="ichiban_kuji",
            item_id="shinchan9-2",
            title="一番くじ 劇場版クレヨンしんちゃん なつかシネマズ",
            url="https://1kuji.com/products/shinchan9-2",
            character="짱구",
            keyword="クレヨンしんちゃん",
            release_text="2026年01月01日発売予定",
        ),
        ReleaseItem(
            source="ichiban_kuji",
            item_id="shinchan9",
            title="一番くじ 劇場版クレヨンしんちゃん なつかシネマズ",
            url="https://1kuji.com/products/shinchan9",
            character="짱구",
            keyword="しんちゃん",
            release_text="2025年01月01日発売予定",
        ),
    ]

    unique = cli._dedupe_in_memory(items)

    assert len(unique) == 1
    assert unique[0].item_id == "shinchan9-2"
