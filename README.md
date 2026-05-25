# Dividend Tracker

보유 종목의 배당 이력을 관리하고 향후 12개월 배당 수입을 예측하는 Django 단일 사용자용 웹 앱.
(클로드 이용해서 vibe 코딩 연습)

## 기능
- Ticker 등록 (yfinance 자동 수집 + 수동 입력)
- 배당 이력 보기/필터/수동 추가
- 보유 포지션 CRUD (보유 수, 평균 단가, 취득일)
- 대시보드: 총 평가액, 연 예상 배당, 평균 yield, 12개월 차트
- 월간 예상 수입 (지급 주기 기반)
- yfinance 동기화 (UI 버튼 + management command)

## 빠른 시작

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # 관리자 페이지 사용 시 (선택)
python manage.py runserver
```

브라우저에서 http://127.0.0.1:8000 접속.

## 주요 URL
| URL | 설명 |
|---|---|
| `/` | 대시보드 |
| `/tickers/` | 종목 목록 |
| `/tickers/add/` | 종목 추가 (자동/수동) |
| `/tickers/<SYMBOL>/` | 종목 상세 + 동기화 |
| `/holdings/` | 보유 CRUD |
| `/dividends/` | 배당 이력 |
| `/projections/` | 12개월 예상 |
| `/admin/` | Django 관리자 |

## CLI 동기화

```bash
python manage.py sync_dividends                 # 전체 종목
python manage.py sync_dividends --symbol AAPL
```

## 스택
Django 5, SQLite, yfinance, django-htmx, Bootstrap 5, Chart.js
