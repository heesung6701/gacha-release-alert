# Gacha Release Alert

반다이 공식 **ガシャポン** 정보와 **一番くじ** 발매 정보를 캐릭터 키워드별로 감시하고, 신규 발매/신규 발견 항목을 Discord 웹훅으로 보내는 MVP입니다.

## MVP 범위

- 캐릭터별 구독 키워드 설정
  - 예: `クレヨンしんちゃん`, `ちいかわ`, `サンリオ`
- 공식 소스 2개 감시
  - Bandai Gashapon: `https://gashapon.jp/products/result.php?free=...`
  - Ichiban Kuji: `https://1kuji.com/search?word=...`
- SQLite로 이미 알림 보낸 상품 dedupe
- Discord webhook으로 신규 상품 embed 알림
- cron/GitHub Actions/서버에서 주기 실행 가능한 CLI

## 빠른 시작

```bash
cd /Users/quokkaman/github/gacha-release-alert
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp config.example.yaml config.yaml
```

`config.yaml`에서 `discord_webhook_url`을 채운 뒤:

```bash
# 실제 디스코드 전송 없이 파싱 결과만 보기
python -m gacha_alert.cli --config config.yaml --dry-run

# 신규 항목을 디스코드로 전송
python -m gacha_alert.cli --config config.yaml
```

## 설정 예시

```yaml
discord_webhook_url: "https://discord.com/api/webhooks/.../..."
database_path: "data/gacha_alert.sqlite3"
subscriptions:
  - character: "짱구"
    keywords:
      - "クレヨンしんちゃん"
      - "しんちゃん"
    sources: ["gashapon", "ichiban_kuji"]
```

## 다음 단계

1. Discord 봇 slash command로 구독 CRUD 제공
2. 캐릭터/키워드 관리용 작은 웹 UI 추가
3. 한국 입고처/매장 제보 데이터 추가
4. 도감/중복 교환 기능과 연결

## 주의

공식 사이트 HTML 구조가 바뀌면 파서가 깨질 수 있습니다. 그래서 `tests/fixtures` 기반 회귀 테스트를 추가하는 것이 다음 우선순위입니다.
