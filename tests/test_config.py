from pathlib import Path

from gacha_alert.config import load_config


def test_load_config_reads_subscriptions_from_separate_filter_file(tmp_path: Path):
    filters = tmp_path / "filters.yaml"
    filters.write_text(
        """
characters:
  - id: shinchan
    label: 짱구
    enabled: true
    keywords:
      - クレヨンしんちゃん
    sources: [gashapon, ichiban_kuji]
  - id: sanrio
    label: 산리오
    enabled: true
    keywords:
      - サンリオ
      - ハローキティ
    sources: [gashapon, ichiban_kuji]
  - id: chiikawa
    label: 치이카와
    enabled: false
    keywords:
      - ちいかわ
    sources: [gashapon]
""".strip(),
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    config.write_text(
        """
discord_webhook_url: ""
database_path: "data/test.sqlite3"
request_timeout_seconds: 10
filters_path: "filters.yaml"
""".strip(),
        encoding="utf-8",
    )

    loaded = load_config(config)

    assert [subscription.character for subscription in loaded.subscriptions] == ["짱구", "산리오"]
    assert loaded.subscriptions[1].keywords == ["サンリオ", "ハローキティ"]
    assert loaded.available_characters[2].label == "치이카와"
    assert loaded.available_characters[2].enabled is False


def test_load_config_supports_legacy_inline_subscriptions(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
discord_webhook_url: ""
database_path: "data/test.sqlite3"
subscriptions:
  - character: 짱구
    keywords: [クレヨンしんちゃん]
    sources: [gashapon]
""".strip(),
        encoding="utf-8",
    )

    loaded = load_config(config)

    assert [subscription.character for subscription in loaded.subscriptions] == ["짱구"]
    assert loaded.available_characters == []
