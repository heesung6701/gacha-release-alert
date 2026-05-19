from gacha_alert.sources import GashaponScraper, IchibanKujiScraper


def test_parse_gashapon_card():
    html = """
    <div class="c-card__list pg-result__list">
      <a href="detail.php?jan_code=4582769979149000" class="c-card__link">
        <p class="c-card__thumb --squre"><img src="https://example.com/item.jpg" /></p>
        <p class="c-card__name">クレヨンしんちゃん babyいたずらマスコット</p>
        <div class="c-card__bottom"><p class="c-card__price"><span class="c-card__price--main">300</span></p></div>
      </a>
    </div>
    """

    items = GashaponScraper().parse(html, character="짱구", keyword="クレヨンしんちゃん")

    assert len(items) == 1
    assert items[0].source == "gashapon"
    assert items[0].item_id == "4582769979149000"
    assert items[0].price == "300円"
    assert items[0].dedupe_key == "gashapon:4582769979149000"


def test_parse_ichiban_kuji_card():
    html = """
    <ul class="itemList">
      <li><a href="/products/shinchan13">
        <img src="https://example.com/kuji.webp" />
        <div class="txtCol">
          <p class="status shop">店頭販売</p>
          <p class="date">2026年08月08日(土)より順次発売予定</p>
          <p class="itemName">一番くじ クレヨンしんちゃん 夏のバケーションだゾ</p>
        </div>
      </a></li>
    </ul>
    """

    items = IchibanKujiScraper().parse(html, character="짱구", keyword="クレヨンしんちゃん")

    assert len(items) == 1
    assert items[0].source == "ichiban_kuji"
    assert items[0].item_id == "shinchan13"
    assert items[0].release_text == "2026年08月08日(土)より順次発売予定"
    assert items[0].status_text == "店頭販売"
    assert items[0].dedupe_key == "ichiban_kuji:shinchan13"
