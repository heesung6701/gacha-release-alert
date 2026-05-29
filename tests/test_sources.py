from gacha_alert.sources import (
    GashaponScraper,
    IchibanKujiScraper,
    KenElephantScraper,
    KitanClubScraper,
    QualiaScraper,
    ReMentScraper,
    TakaraTomyArtsScraper,
    ToysCabinScraper,
)


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


def test_parse_takara_tomy_arts_search_result():
    html = """
    <a href="/click?url=https%3A%2F%2Fwww.takaratomy-arts.co.jp%2Fitems%2Fitem.html%3Fn%3DY903595">
      サンリオキャラクターズ ビビッドネオンピンバッジ｜商品情報｜タカラトミーアーツ
    </a>
    """

    items = TakaraTomyArtsScraper().parse(html, character="산리오", keyword="サンリオ")

    assert len(items) == 1
    assert items[0].source == "takaratomy_arts"
    assert items[0].item_id == "Y903595"
    assert items[0].title == "サンリオキャラクターズ ビビッドネオンピンバッジ"
    assert items[0].dedupe_key == "takaratomy_arts:Y903595"


def test_parse_qualia_product_links_and_detail():
    listing_html = """
    <div class="list_gacha">
      <a href="https://qualia-45.jp/distinations/niccolino_chuka_nuin/">
        <img src="https://example.com/item.jpg" />
      </a>
    </div>
    """
    detail_html = """
    <html><head><title>にっこりーノ　NEW中華料理のぬいぐるみ | Qualia</title></head>
    <body>
      <h1>にっこりーノ　NEW中華料理のぬいぐるみ</h1>
      <p>発売日：2026年5月</p>
      <p>価格　：400円　全6種</p>
      <h2>Lineup</h2><p>ももまん</p><p>餃子</p>
      <img src="https://example.com/qualia.jpg" />
    </body></html>
    """

    scraper = QualiaScraper()
    links = scraper.parse(listing_html, character="기타", keyword="にっこりーノ")
    detail = scraper.parse_detail(
        detail_html,
        url="https://qualia-45.jp/distinations/niccolino_chuka_nuin/",
        character="기타",
        keyword="にっこりーノ",
    )

    assert links[0].item_id == "niccolino_chuka_nuin"
    assert detail.source == "qualia"
    assert detail.release_text == "2026年5月"
    assert detail.price == "400円　全6種"
    assert detail.lineup_names[:2] == ["ももまん", "餃子"]


def test_parse_ken_elephant_products_json():
    products = [
        {
            "id": 123,
            "title": "PEZ×はぴだんぶい マスコット",
            "handle": "gc0714c",
            "body_html": "<p>サンリオキャラクターズのミニチュアコレクション</p>",
            "images": [{"src": "https://example.com/ken.jpg"}],
            "variants": [{"price": "500", "available": True}],
            "tags": ["ミニチュアコレクション"],
        }
    ]

    items = KenElephantScraper().parse_products(products, character="산리오", keyword="サンリオ")

    assert len(items) == 1
    assert items[0].source == "ken_elephant"
    assert items[0].item_id == "123"
    assert items[0].url == "https://kenelestore.jp/products/gc0714c"
    assert items[0].price == "¥500"


def test_parse_kitan_club_product_detail():
    html = """
    <section class="c-productDetail">
      <h2 class="c-productDetail__title">ちいかわ みんな大集合！フィギュア20体セット</h2>
      <div class="c-productDetail__thum"><img src="https://example.com/kitan.jpg" /></div>
      <div class="c-productDetail__text">ちいかわのフィギュアセットです。</div>
      <dl class="c-productDetail__detail-item"><dt>商品名</dt><dd>ちいかわ みんな大集合！フィギュア20体セット</dd></dl>
      <dl class="c-productDetail__detail-item"><dt>発売日</dt><dd>2026年5月下旬</dd></dl>
      <dl class="c-productDetail__detail-item"><dt>価格</dt><dd>1回500円 全5種</dd></dl>
    </section>
    """

    item = KitanClubScraper().parse_detail(
        html,
        url="https://kitan.jp/products/chiikawa_figures/",
        character="치이카와",
        keyword="ちいかわ",
    )

    assert item.source == "kitan_club"
    assert item.item_id == "chiikawa_figures"
    assert item.price == "1回500円 全5種"
    assert item.release_text == "2026年5月下旬"


def test_parse_toys_cabin_listing():
    html = """
    <a href="/product/20260501_1421.php">
      <img src="/uploads/fgo.jpg" />
      Fate/Grand Order 概念礼装カードアクリル＆キーホルダー　300円
      2026年8月　JAN CODE:4589415443597
    </a>
    """

    items = ToysCabinScraper().parse(html, character="FGO", keyword="Fate/Grand Order")

    assert len(items) == 1
    assert items[0].source == "toys_cabin"
    assert items[0].item_id == "20260501_1421"
    assert items[0].price == "300円"
    assert items[0].release_text == "2026年8月"


def test_parse_rement_brand_page():
    html = """
    <div class="item">
      <a href="../product/r70006">
        <p class="photo"><img data-original="../images/item/r70006.jpg" /></p>
        <p class="name">シナモロール　きらきらそらいろパーティー</p>
        <p class="price">1,320円（税抜価格1,200円）</p>
        <p>発売予定</p>
      </a>
    </div>
    """

    items = ReMentScraper().parse(html, character="산리오", keyword="シナモロール")

    assert len(items) == 1
    assert items[0].source == "rement"
    assert items[0].item_id == "r70006"
    assert items[0].status_text == "発売予定"
