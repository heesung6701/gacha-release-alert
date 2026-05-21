from gacha_alert.korean import translate_release_text, translate_status_text, translate_title


def test_translate_title_rewrites_common_japanese_product_terms_to_korean():
    assert translate_title("一番くじ クレヨンしんちゃん 夏のバケーションだゾ") == "이치방쿠지 짱구는 못말려 여름 바캉스다"
    assert translate_title("クレヨンしんちゃん ライトマスコット３") == "짱구는 못말려 라이트 마스코트3"


def test_translate_release_and_status_text_to_korean():
    assert translate_release_text("2026年08月08日(土)より順次発売予定") == "2026년 08월 08일(토)부터 순차 발매 예정"
    assert translate_status_text("店頭販売 / オンライン販売") == "매장 판매 / 온라인 판매"
