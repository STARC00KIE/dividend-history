"""Wrapper around yfinance for fetching ticker info, dividends, and quotes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable

import yfinance as yf

from ..models import DividendFrequency


class YFinanceError(Exception):
    pass


@dataclass
class DividendRecord:
    ex_date: date
    amount_per_share: Decimal


@dataclass
class TickerInfo:
    symbol: str
    name: str
    currency: str
    dividend_frequency: str


def _infer_frequency(ex_dates: Iterable[date]) -> str:
    dates = sorted(set(ex_dates))
    if len(dates) < 2:
        return DividendFrequency.IRREGULAR
    recent = dates[-min(8, len(dates)):]
    if len(recent) < 2:
        return DividendFrequency.IRREGULAR
    gaps = [(recent[i] - recent[i - 1]).days for i in range(1, len(recent))]
    avg = sum(gaps) / len(gaps)
    if avg <= 45:
        return DividendFrequency.MONTHLY
    if avg <= 110:
        return DividendFrequency.QUARTERLY
    if avg <= 220:
        return DividendFrequency.SEMI_ANNUAL
    if avg <= 450:
        return DividendFrequency.ANNUAL
    return DividendFrequency.IRREGULAR


def fetch_ticker_info(symbol: str) -> TickerInfo:
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}
        dividends = t.dividends
    except Exception as exc:  # network/parsing
        raise YFinanceError(f"yfinance failed for {symbol}: {exc}") from exc

    name = info.get("longName") or info.get("shortName") or symbol
    currency = info.get("currency") or "USD"

    ex_dates: list[date] = []
    if dividends is not None and len(dividends) > 0:
        for idx in dividends.index:
            d = idx.date() if hasattr(idx, "date") else idx
            ex_dates.append(d)
    frequency = _infer_frequency(ex_dates)

    return TickerInfo(
        symbol=symbol.upper(),
        name=name,
        currency=currency,
        dividend_frequency=frequency,
    )


def fetch_dividend_history(symbol: str, since: date | None = None) -> list[DividendRecord]:
    try:
        dividends = yf.Ticker(symbol).dividends
    except Exception as exc:
        raise YFinanceError(f"yfinance failed for {symbol}: {exc}") from exc

    records: list[DividendRecord] = []
    if dividends is None or len(dividends) == 0:
        return records

    for idx, amount in dividends.items():
        d = idx.date() if hasattr(idx, "date") else idx
        if since is not None and d < since:
            continue
        records.append(
            DividendRecord(
                ex_date=d,
                amount_per_share=Decimal(str(round(float(amount), 6))),
            )
        )
    records.sort(key=lambda r: r.ex_date)
    return records


def fetch_quote(symbol: str) -> Decimal:
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="1d")
        if hist is not None and len(hist) > 0:
            price = float(hist["Close"].iloc[-1])
            return Decimal(str(round(price, 4)))
        info = t.info or {}
        price = info.get("regularMarketPrice") or info.get("previousClose")
        if price is None:
            raise YFinanceError(f"No price available for {symbol}")
        return Decimal(str(round(float(price), 4)))
    except YFinanceError:
        raise
    except Exception as exc:
        raise YFinanceError(f"yfinance failed for {symbol}: {exc}") from exc
