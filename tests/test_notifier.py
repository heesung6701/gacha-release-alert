from gacha_alert.models import ReleaseItem
from gacha_alert.notifier import DiscordNotifier


def test_discord_payload_includes_gashapon_detail_fields():
    item = ReleaseItem(
        source="gashapon",
        item_id="4582769979149000",
        title="クレヨンしんちゃん babyいたずらマスコット",
        url="https://gashapon.jp/products/detail.php?jan_code=4582769979149000",
        character="짱구",
        keyword="クレヨンしんちゃん",
        image_url="https://example.com/main.jpg",
        price="300円",
        release_text="2026年5月 第5週",
        status_text="全5種 / 15才以上",
        description="babyのカスカベ防衛隊が、いたずらをしてしまう…！",
        lineup_names=["しんちゃん", "かざまくん"],
    )

    payload = DiscordNotifier("https://discord.com/api/webhooks/1/token")._payload(item)

    embed = payload["embeds"][0]
    field_values = {field["name"]: field["value"] for field in embed["fields"]}
    assert embed["description"] == "babyのカスカベ防衛隊が、いたずらをしてしまう…！"
    assert field_values["라인업"] == "しんちゃん, かざまくん"
    assert field_values["발매/판매 정보"] == "2026年5月 第5週"
    assert field_values["가격"] == "300円"
