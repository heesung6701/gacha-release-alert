from gacha_alert.models import ReleaseItem
from gacha_alert.sources import GashaponScraper


DETAIL_HTML = """
<main class="l-main">
  <div class="pg-detail">
    <h1 class="pg-heading">クレヨンしんちゃん babyいたずらマスコット</h1>
    <div class="pg-detail__picture js-swiper" data-swiper="main">
      <ul class="swiper-wrapper">
        <li class="swiper-slide"><img src="https://example.com/main.jpg" title="" alt=""></li>
        <li class="swiper-slide"><img src="https://example.com/shinchan.jpg" title="しんちゃん" alt=""></li>
        <li class="swiper-slide"><img src="https://example.com/kazama.jpg" title="かざまくん" alt=""></li>
      </ul>
    </div>
    <p class="pg-detail__description">babyのカスカベ防衛隊が、いたずらをしてしまう…！</p>
    <div class="pg-detailDefinition__wrap">
      <dl class="pg-detailDefinition">
        <dt class="pg-detailDefinition__title">発売時期</dt>
        <dd class="pg-detailDefinition__detail --releaseDate">2026年5月 第5週 <br /></dd>
      </dl>
      <dl class="pg-detailDefinition">
        <dt class="pg-detailDefinition__title">価格(税込)</dt>
        <dd class="pg-detailDefinition__detail">300円</dd>
      </dl>
      <dl class="pg-detailDefinition">
        <dt class="pg-detailDefinition__title">種類数</dt>
        <dd class="pg-detailDefinition__detail">全5種</dd>
      </dl>
      <dl class="pg-detailDefinition">
        <dt class="pg-detailDefinition__title">対象年齢</dt>
        <dd class="pg-detailDefinition__detail">15才以上</dd>
      </dl>
    </div>
  </div>
</main>
"""


def test_parse_gashapon_detail_extracts_release_metadata_and_lineup_names():
    detail = GashaponScraper().parse_detail(DETAIL_HTML)

    assert detail.title == "クレヨンしんちゃん babyいたずらマスコット"
    assert detail.description == "babyのカスカベ防衛隊が、いたずらをしてしまう…！"
    assert detail.release_text == "2026年5月 第5週"
    assert detail.price == "300円"
    assert detail.kind_count == "全5種"
    assert detail.target_age == "15才以上"
    assert detail.lineup_names == ["しんちゃん", "かざまくん"]
    assert detail.image_urls == [
        "https://example.com/main.jpg",
        "https://example.com/shinchan.jpg",
        "https://example.com/kazama.jpg",
    ]


def test_enrich_gashapon_item_uses_detail_metadata_without_changing_identity():
    item = ReleaseItem(
        source="gashapon",
        item_id="4582769979149000",
        title="クレヨンしんちゃん babyいたずらマスコット",
        url="https://gashapon.jp/products/detail.php?jan_code=4582769979149000",
        character="짱구",
        keyword="クレヨンしんちゃん",
        image_url="https://example.com/search.jpg",
    )
    detail = GashaponScraper().parse_detail(DETAIL_HTML)

    enriched = GashaponScraper().enrich_item(item, detail)

    assert enriched.dedupe_key == item.dedupe_key
    assert enriched.release_text == "2026年5月 第5週"
    assert enriched.price == "300円"
    assert enriched.status_text == "全5種 / 15才以上"
    assert enriched.description == "babyのカスカベ防衛隊が、いたずらをしてしまう…！"
    assert enriched.lineup_names == ["しんちゃん", "かざまくん"]
    assert enriched.image_url == "https://example.com/main.jpg"
