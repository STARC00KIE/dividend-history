"""Monthly dividend income projection."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from ..models import DividendFrequency, FREQUENCY_PAYMENTS_PER_YEAR, Holding


@dataclass
class MonthlyIncome:
    year: int
    month: int
    amount: Decimal

    @property
    def label(self) -> str:
        return f"{self.year}-{self.month:02d}"


def _next_payment_months(latest_ex_date: date, frequency: str, months_ahead: int) -> list[date]:
    """Return the first day of each projected payment month within `months_ahead` from today."""
    today = date.today().replace(day=1)
    end = today + relativedelta(months=months_ahead)

    payments_per_year = FREQUENCY_PAYMENTS_PER_YEAR.get(frequency, 0)
    if payments_per_year == 0:
        return []

    interval_months = 12 // payments_per_year
    anchor = latest_ex_date.replace(day=1)
    # Step forward until we're within the projection window
    while anchor < today:
        anchor += relativedelta(months=interval_months)

    months: list[date] = []
    cursor = anchor
    while cursor < end:
        months.append(cursor)
        cursor += relativedelta(months=interval_months)
    return months


def monthly_projection(holdings, months: int = 12) -> list[MonthlyIncome]:
    today = date.today().replace(day=1)
    buckets: OrderedDict[tuple[int, int], Decimal] = OrderedDict()
    for i in range(months):
        d = today + relativedelta(months=i)
        buckets[(d.year, d.month)] = Decimal("0")

    for holding in holdings:
        ticker = holding.ticker
        latest = ticker.latest_dividend
        if latest is None:
            continue
        frequency = ticker.dividend_frequency

        if frequency == DividendFrequency.IRREGULAR:
            # 최근 12개월 합계를 균등 분배
            annual = ticker.annualized_dividend * holding.shares
            per_month = (annual / Decimal(months)).quantize(Decimal("0.01"))
            for key in buckets:
                buckets[key] += per_month
            continue

        payment_months = _next_payment_months(latest.ex_date, frequency, months)
        per_payment = (latest.amount_per_share * holding.shares).quantize(Decimal("0.01"))
        for pm in payment_months:
            key = (pm.year, pm.month)
            if key in buckets:
                buckets[key] += per_payment

    return [MonthlyIncome(year=y, month=m, amount=amt) for (y, m), amt in buckets.items()]
