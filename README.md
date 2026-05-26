# Gacha Release Alert

반다이 공식 **ガシャポン** 정보와 **一番くじ** 발매 정보를 캐릭터 키워드별로 감시하고, 신규 발매/신규 발견 항목을 Discord 웹훅으로 보내는 MVP입니다.

## MVP 범위

- 캐릭터별 구독 키워드 설정
  - 예: `クレヨンしんちゃん`, `ちいかわ`, `サンリオ`
- 공식 소스 5개 감시
  - Bandai Gashapon: `https://gashapon.jp/products/result.php?free=...`
  - Ichiban Kuji: `https://1kuji.com/search?word=...`
  - Takara Tomy Arts: `https://search.takaratomy-arts.co.jp/search?...`
  - Qualia: `https://qualia-45.jp/products/`
  - Ken Elephant: `https://kenelestore.jp/collections/miniature__latest/products.json?...`
- SQLite로 이미 알림 보낸 상품 dedupe
- Discord webhook으로 신규 상품 embed 알림
  - Gashapon은 상세 페이지에서 발매시기/가격/종류수/대상연령/설명/라인업명을 보강
- GitHub Actions cron으로 주기 수집 후 `public/data/releases.json` 커밋
- 커밋된 JSON을 기반으로 GitHub Pages 정적 대시보드 배포
- cron/GitHub Actions/서버에서 주기 실행 가능한 CLI

## 빠른 시작

```bash
cd /Users/quokkaman/github/gacha-release-alert
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp config.example.yaml config.yaml
cp filters.example.yaml filters.yaml
```

`config.yaml`에서 `discord_webhook_url`을 채우고, `filters_path`가 `filters.yaml`을 가리키게 둡니다.
`filters.yaml`에서는 알림 받을 캐릭터만 `enabled: true`로 체크하면 됩니다.

```bash
# 실제 디스코드 전송 없이 파싱 결과만 보기
python -m gacha_alert.cli --config config.yaml --dry-run

# 신규 항목을 디스코드로 전송
python -m gacha_alert.cli --config config.yaml

# GitHub Pages용 정적 JSON 생성
python -m gacha_alert.cli --config config.pages.yaml --export-json public/data/releases.json
```

## GitHub Pages 대시보드

`.github/workflows/pages.yml`은 6시간마다 공식 사이트 데이터를 가져와 `public/data/releases.json`을 갱신하고, 변경이 있을 때만 해당 JSON을 `main`에 커밋한 뒤 `public/` 디렉터리를 GitHub Pages로 배포합니다. `push` 이벤트에서는 이미 커밋된 `public/` 내용을 그대로 배포하므로, Pages는 저장소에 남은 데이터 스냅샷을 기준으로 구성됩니다.

1. GitHub 저장소 Settings → Pages → Source를 **GitHub Actions**로 설정합니다.
2. Actions 탭에서 **Fetch gacha releases and deploy Pages** 워크플로우를 수동 실행하거나, `main`에 push하면 자동 배포됩니다.
3. 스케줄 실행에서 데이터가 바뀌면 `chore: update gacha release data` 커밋이 자동으로 생깁니다. `public/data/releases.json`은 로컬 `data/` 캐시 ignore 규칙과 충돌하지 않도록 workflow에서 명시적으로 stage합니다. 데이터가 같으면 `generated_at`도 유지되어 불필요한 커밋이 생기지 않습니다.
4. 배포 후 Pages URL에서 캐릭터/소스/검색어 필터로 최신 항목을 볼 수 있습니다.

## 설정 예시

`config.yaml`은 실행 환경/비밀값만 둡니다.

```yaml
discord_webhook_url: "https://discord.com/api/webhooks/.../..."
webhook_secret: ""  # Hermes 웹훅을 쓰면 HMAC secret 입력
database_path: "data/gacha_alert.sqlite3"
request_timeout_seconds: 20
filters_path: "filters.yaml"
```

`filters.yaml`은 캐릭터 필터 목록입니다. 체크박스 UI의 데이터 소스처럼 쓰기 위해 `enabled` 값을 둡니다.

```yaml
characters:
  - id: "shinchan"
    label: "짱구"
    enabled: true
    keywords:
      - "クレヨンしんちゃん"
      - "しんちゃん"
    sources: ["gashapon", "ichiban_kuji"]

  - id: "sanrio"
    label: "산리오"
    enabled: true
    keywords:
      - "サンリオ"
      - "ハローキティ"
      - "シナモロール"
      - "マイメロディ"
      - "クロミ"
      - "ポムポムプリン"
    sources: ["gashapon", "ichiban_kuji"]

  - id: "chiikawa"
    label: "치이카와"
    enabled: false
    keywords: ["ちいかわ"]
    sources: ["gashapon", "ichiban_kuji"]
```

기존처럼 `config.yaml`에 `subscriptions`를 직접 넣는 방식도 아직 지원하지만, 앞으로는 `filters.yaml` 방식이 기본입니다.

## 다음 단계

1. Discord 봇 slash command로 구독 CRUD 제공
2. 캐릭터/키워드 관리용 작은 웹 UI 추가
3. 한국 입고처/매장 제보 데이터 추가
4. 도감/중복 교환 기능과 연결

## 주의

공식 사이트 HTML 구조가 바뀌면 파서가 깨질 수 있습니다. 그래서 `tests/fixtures` 기반 회귀 테스트를 추가하는 것이 다음 우선순위입니다.
