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
    assert payload["items"][0]["character"] == "짱구"
