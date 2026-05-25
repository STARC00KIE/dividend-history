"""High-level sync orchestration that ties yfinance fetches to the database."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from ..models import Dividend, Quote, Ticker
from . import yfinance_client


@dataclass
class SyncResult:
    ticker: Ticker
    new_dividends: int
    price: object | None


def sync_ticker(ticker: Ticker) -> SyncResult:
    info = yfinance_client.fetch_ticker_info(ticker.symbol)
    ticker.name = info.name or ticker.name
    ticker.currency = info.currency or ticker.currency
    if info.dividend_frequency:
        ticker.dividend_frequency = info.dividend_frequency

    records = yfinance_client.fetch_dividend_history(ticker.symbol)
    new_count = 0
    for r in records:
        _, created = Dividend.objects.update_or_create(
            ticker=ticker,
            ex_date=r.ex_date,
            defaults={
                "amount_per_share": r.amount_per_share,
                "source": Dividend.Source.YFINANCE,
            },
        )
        if created:
            new_count += 1

    price = None
    try:
        price = yfinance_client.fetch_quote(ticker.symbol)
        Quote.objects.update_or_create(ticker=ticker, defaults={"price": price})
    except yfinance_client.YFinanceError:
        price = None

    ticker.last_synced_at = timezone.now()
    ticker.save()

    return SyncResult(ticker=ticker, new_dividends=new_count, price=price)
