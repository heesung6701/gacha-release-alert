# Architecture

## Product concept

캐릭터별로 반다이 공식 가챠/이치방쿠지 발매 정보를 구독하고 Discord로 알려주는 서비스.

초기 타깃은 `짱구(クレヨンしんちゃん)` 수집가입니다. 이후 다른 캐릭터 키워드만 추가하면 확장됩니다.

## Data flow

```text
config.yaml subscriptions
  -> source scraper per keyword
  -> normalize ReleaseItem
  -> SQLite seen_items dedupe
  -> Discord webhook embed
```

## Sources

### Bandai Gashapon

- Search URL: `https://gashapon.jp/products/result.php?free={keyword}`
- 현재 확인한 카드 구조:
  - `div.c-card__list`
  - detail: `a.c-card__link[href="detail.php?jan_code=..."]`
  - title: `.c-card__name`
  - price: `.c-card__price--main`
  - image: `.c-card__thumb img[src]`
- release date는 검색 카드에 명확히 없을 수 있으므로 MVP에서는 `unknown` 처리. 필요하면 detail page 추가 fetch.

### Ichiban Kuji

- Search URL: `https://1kuji.com/search?word={keyword}`
- 현재 확인한 카드 구조:
  - `ul.itemList li`
  - detail: `a[href^="/products/"]`
  - title: `.itemName`
  - release/status: `.status`, `.date`
  - image: `img[src]`

## Dedupe key

`source:item_id`를 유니크키로 사용합니다.

- Gashapon: `jan_code`가 있으면 `gashapon:{jan_code}`
- Ichiban Kuji: product slug, 예: `ichiban_kuji:shinchan13`

## Discord notification

각 신규 항목을 embed 하나로 보냅니다.

- title: 상품명
- URL: 공식 상세 페이지
- description: source, character, release/status, price
- image: 공식 썸네일

## Deployment options

MVP는 cron으로 충분합니다.

```cron
*/30 * * * * cd /Users/quokkaman/github/gacha-release-alert && .venv/bin/python -m gacha_alert.cli --config config.yaml
```

나중에 Discord 봇으로 확장하면:

- `/subscribe character:짱구 keyword:クレヨンしんちゃん`
- `/unsubscribe character:짱구`
- `/list-subscriptions`

명령을 추가합니다.
