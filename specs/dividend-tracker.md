# Dividend Tracker App — Specification

## Context

보유 종목의 배당 이력과 수익률(yield)을 관리하고, 월별 배당 수입을 예측할 수 있는 개인용 Django 웹 애플리케이션.

확정된 요구사항:
- **백엔드**: Django + SQLite
- **UI**: Django Templates (Bootstrap 5 + HTMX로 가벼운 동적 인터랙션)
- **데이터 소스**: `yfinance`로 자동 수집 + 수동 입력/수정 동시 지원
- **예측 방식**: 최근 배당금 × 보유 수를 지급 주기(월/분기/연)에 맞춰 12개월에 분배하는 단순 예측
- **사용자 모델**: 단일 사용자, 인증 없음 (로컬 개인 사용)

## Tech Stack

- Python 3.11+, Django 5.x
- SQLite (기본 `db.sqlite3`)
- `yfinance` — Yahoo Finance에서 ticker 정보 및 배당 이력 수집
- `django-htmx` — 부분 페이지 갱신 (테이블 새로고침, 폼 검증)
- Bootstrap 5 (CDN) — 스타일링
- `python-dateutil` — 배당 주기 계산용

## Project Layout

```
dividend-history/
├── manage.py
├── requirements.txt
├── README.md
├── config/                  # Django 프로젝트 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tracker/                 # 메인 앱
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── services/
│   │   ├── yfinance_client.py   # 외부 데이터 수집 래퍼
│   │   └── projections.py       # 월간 수입 예측 계산
│   ├── templates/tracker/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── ticker_list.html
│   │   ├── ticker_detail.html
│   │   ├── dividend_list.html
│   │   └── partials/...         # HTMX 부분 템플릿
│   └── management/commands/
│       └── sync_dividends.py    # 수동 동기화 커맨드
└── static/                  # 정적 파일 (필요 시)
```

## Data Model (`tracker/models.py`)

1. **`Ticker`** — 종목 마스터
   - `symbol` (CharField, unique, e.g. "AAPL")
   - `name` (CharField)
   - `currency` (CharField, default "USD")
   - `dividend_frequency` (CharField choices: `MONTHLY` / `QUARTERLY` / `SEMI_ANNUAL` / `ANNUAL` / `IRREGULAR`)
   - `last_synced_at` (DateTimeField, nullable)
   - `created_at`, `updated_at`

2. **`Holding`** — 보유 포지션
   - `ticker` (FK → Ticker, on_delete=CASCADE)
   - `shares` (DecimalField, max_digits=12, decimal_places=4)
   - `average_cost` (DecimalField, nullable) — yield-on-cost 계산용
   - `acquired_at` (DateField, nullable)
   - `notes` (TextField, blank)

3. **`Dividend`** — 배당 지급 이력
   - `ticker` (FK → Ticker, on_delete=CASCADE)
   - `ex_date` (DateField)
   - `pay_date` (DateField, nullable)
   - `amount_per_share` (DecimalField, max_digits=10, decimal_places=6)
   - `source` (CharField choices: `YFINANCE` / `MANUAL`)
   - `unique_together = [("ticker", "ex_date")]`

4. **`Quote`** — 최신 주가 캐시
   - `ticker` (OneToOne → Ticker)
   - `price` (DecimalField)
   - `fetched_at` (DateTimeField)
   - yield(%) 계산은 `(연환산 배당 / 현재가) × 100`로 즉석 계산

## Core Features & Views

| URL | View | 역할 |
|---|---|---|
| `/` | `dashboard` | 총 평가액, 연 예상 배당, 평균 yield, 다음 12개월 막대 차트 |
| `/tickers/` | `ticker_list` | 등록된 ticker 목록 |
| `/tickers/add/` | `ticker_add` | symbol 입력 → yfinance로 메타데이터 자동 채움, 실패 시 수동 |
| `/tickers/<symbol>/` | `ticker_detail` | 종목 상세, 배당 이력 테이블, 동기화 버튼 (HTMX) |
| `/tickers/<symbol>/sync/` | `ticker_sync` (POST) | yfinance 재호출 → Dividend/Quote 갱신 |
| `/holdings/` | `holding_list` | 보유 종목 CRUD |
| `/dividends/` | `dividend_list` | 전체 배당 이력 |
| `/dividends/add/` | `dividend_add` | 수동 배당 추가 |
| `/projections/` | `projection_view` | 월별 예상 수입 (12개월) 표 + 차트 |

## Services Layer

### `services/yfinance_client.py`
- `fetch_ticker_info(symbol) -> dict` — 이름/통화/지급 주기 추정
- `fetch_dividend_history(symbol, since=None)`
- `fetch_quote(symbol) -> Decimal`

### `services/projections.py`
- `monthly_projection(holdings, months=12)`
  - 각 holding마다 가장 최근 배당 1건 사용
  - `dividend_frequency`에 따라 다음 12개월 지급 월 추정
  - `IRREGULAR`은 최근 12개월 합계를 12로 균등 분배
  - `amount_per_share × shares` 누적

## Configuration Notes
- `INSTALLED_APPS`: `tracker`, `django_htmx`
- `TIME_ZONE = "Asia/Seoul"`, `USE_TZ = True`
- 단일 사용자이므로 인증 미사용. Admin은 `createsuperuser`로 접근.
- `requirements.txt`: `Django>=5.0`, `yfinance`, `django-htmx`, `python-dateutil`

## Verification

- **모델 단위**: shell에서 Ticker → Holding → Dividend 생성 후 `projections.monthly_projection()` 결과 검증
- **yfinance**: `python manage.py sync_dividends --symbol AAPL` 실행 후 admin 확인
- **UI 골든 패스**:
  1. `/tickers/add/`에 `KO` 입력 → 자동 채움
  2. `/holdings/`에서 10주 등록
  3. `/projections/`에서 12개월 예상 수입 확인
  4. `/dividends/add/`로 과거 배당 수동 추가 → 목록 반영
  5. `/tickers/<symbol>/sync/` HTMX 동기화 확인
