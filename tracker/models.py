from decimal import Decimal

from django.db import models


class DividendFrequency(models.TextChoices):
    MONTHLY = "MONTHLY", "Monthly"
    QUARTERLY = "QUARTERLY", "Quarterly"
    SEMI_ANNUAL = "SEMI_ANNUAL", "Semi-Annual"
    ANNUAL = "ANNUAL", "Annual"
    IRREGULAR = "IRREGULAR", "Irregular"


FREQUENCY_PAYMENTS_PER_YEAR = {
    DividendFrequency.MONTHLY: 12,
    DividendFrequency.QUARTERLY: 4,
    DividendFrequency.SEMI_ANNUAL: 2,
    DividendFrequency.ANNUAL: 1,
    DividendFrequency.IRREGULAR: 0,
}


class Ticker(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    dividend_frequency = models.CharField(
        max_length=20,
        choices=DividendFrequency.choices,
        default=DividendFrequency.QUARTERLY,
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self) -> str:
        return self.symbol

    @property
    def latest_dividend(self):
        return self.dividends.order_by("-ex_date").first()

    @property
    def annualized_dividend(self) -> Decimal:
        latest = self.latest_dividend
        if latest is None:
            return Decimal("0")
        payments = FREQUENCY_PAYMENTS_PER_YEAR.get(self.dividend_frequency, 0)
        if payments == 0:
            from datetime import date, timedelta

            cutoff = date.today() - timedelta(days=365)
            total = self.dividends.filter(ex_date__gte=cutoff).aggregate(
                total=models.Sum("amount_per_share")
            )["total"] or Decimal("0")
            return total
        return latest.amount_per_share * payments

    @property
    def current_yield(self):
        quote = getattr(self, "quote", None)
        if quote is None or quote.price == 0:
            return None
        return (self.annualized_dividend / quote.price) * Decimal("100")


class Holding(models.Model):
    ticker = models.ForeignKey(
        Ticker, on_delete=models.CASCADE, related_name="holdings"
    )
    shares = models.DecimalField(max_digits=14, decimal_places=4)
    average_cost = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    acquired_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ticker__symbol"]

    def __str__(self) -> str:
        return f"{self.ticker.symbol} × {self.shares}"

    @property
    def market_value(self):
        quote = getattr(self.ticker, "quote", None)
        if quote is None:
            return None
        return quote.price * self.shares

    @property
    def annual_income(self) -> Decimal:
        return self.ticker.annualized_dividend * self.shares

    @property
    def yield_on_cost(self):
        if not self.average_cost or self.average_cost == 0:
            return None
        return (self.ticker.annualized_dividend / self.average_cost) * Decimal("100")


class Dividend(models.Model):
    class Source(models.TextChoices):
        YFINANCE = "YFINANCE", "yfinance"
        MANUAL = "MANUAL", "Manual"

    ticker = models.ForeignKey(
        Ticker, on_delete=models.CASCADE, related_name="dividends"
    )
    ex_date = models.DateField()
    pay_date = models.DateField(null=True, blank=True)
    amount_per_share = models.DecimalField(max_digits=12, decimal_places=6)
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MANUAL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ex_date"]
        unique_together = [("ticker", "ex_date")]

    def __str__(self) -> str:
        return f"{self.ticker.symbol} {self.ex_date} ${self.amount_per_share}"


class Quote(models.Model):
    ticker = models.OneToOneField(
        Ticker, on_delete=models.CASCADE, related_name="quote"
    )
    price = models.DecimalField(max_digits=14, decimal_places=4)
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.ticker.symbol} @ {self.price}"
