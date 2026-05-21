from __future__ import annotations

import re

_TITLE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("クレヨンしんちゃん", "짱구는 못말려"),
    ("一番くじ", "이치방쿠지"),
    ("劇場版", "극장판"),
    ("映画", "영화"),
    ("夏のバケーションだゾ", "여름 바캉스다"),
    ("アニメシーンセレクションだゾ", "애니메이션 장면 셀렉션이다"),
    ("オラお腹いっぱいだゾ", "나 배불러요"),
    ("なつかシネマズ", "추억의 시네마즈"),
    ("名作シネマズ", "명작 시네마즈"),
    ("チョコビがおいしいゾ", "초코비가 맛있다"),
    ("オラとおでかけだゾ", "나랑 외출이다"),
    ("ヘンダーランドの大冒険", "헨더랜드의 대모험"),
    ("嵐を呼ぶ", "폭풍을 부르는"),
    ("栄光のヤキニクロード", "영광의 야키니쿠로드"),
    ("サンリオ", "산리오"),
    ("ハローキティ", "헬로키티"),
    ("シナモロール", "시나모롤"),
    ("マイメロディ", "마이멜로디"),
    ("クロミ", "쿠로미"),
    ("ポムポムプリン", "폼폼푸린"),
    ("ライトマスコット", "라이트 마스코트"),
    ("マスコット", "마스코트"),
    ("コレクション", "컬렉션"),
    ("アクセサリー", "액세서리"),
    ("チャーム", "참"),
    ("ライト", "라이트"),
    ("ミニチュア", "미니어처"),
    ("パッケージ", "패키지"),
    ("ミラー", "거울"),
    ("サウンド", "사운드"),
    ("カラー", "컬러"),
    ("パステル", "파스텔"),
    ("オンライン", "온라인"),
)

_STATUS_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("店頭販売", "매장 판매"),
    ("オンライン販売", "온라인 판매"),
    ("販売", "판매"),
)

_WEEKDAYS = {
    "月": "월",
    "火": "화",
    "水": "수",
    "木": "목",
    "金": "금",
    "土": "토",
    "日": "일",
}


def translate_title(title: str | None) -> str | None:
    if not title:
        return title
    translated = title
    for source, target in _TITLE_REPLACEMENTS:
        translated = translated.replace(source, target)
    translated = translated.replace("～", " ").replace("★", "").replace("！", "!")
    translated = re.sub(r"([A-Za-z가-힣])([0-9０-９]+)", r"\1\2", translated)
    translated = _normalize_japanese_digits(translated)
    return _normalize_spaces(translated)


def translate_release_text(text: str | None) -> str | None:
    if not text:
        return text
    translated = _translate_dates(text)
    translated = translated.replace("より順次発売予定", "부터 순차 발매 예정")
    translated = translated.replace("より販売開始予定", "부터 판매 시작 예정")
    translated = translated.replace("販売開始予定", "판매 시작 예정")
    translated = translated.replace("発売予定", "발매 예정")
    translated = translated.replace("【予約販売期間】", "【예약 판매 기간】")
    translated = translated.replace("～", "~")
    return _normalize_spaces(translated)


def translate_status_text(text: str | None) -> str | None:
    if not text:
        return text
    translated = text
    for source, target in _STATUS_REPLACEMENTS:
        translated = translated.replace(source, target)
    return _normalize_spaces(translated)


def translated_release_dict(item_dict: dict) -> dict:
    translated = dict(item_dict)
    translated["title_ko"] = translate_title(item_dict.get("title"))
    translated["release_text_ko"] = translate_release_text(item_dict.get("release_text"))
    translated["status_text_ko"] = translate_status_text(item_dict.get("status_text"))
    return translated


def _translate_dates(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        year, month, day, weekday = match.groups()
        return f"{year}년 {month}월 {day}일({_WEEKDAYS[weekday]})"

    return re.sub(r"(\d{4})年(\d{2})月(\d{2})日\(([月火水木金土日])\)", repl, text)


def _normalize_japanese_digits(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def _normalize_spaces(text: str) -> str:
    return " ".join(text.split())
