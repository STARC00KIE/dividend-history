from django.core.management.base import BaseCommand, CommandError

from tracker.models import Ticker
from tracker.services import sync as sync_service
from tracker.services.yfinance_client import YFinanceError


class Command(BaseCommand):
    help = "Sync ticker metadata, dividend history, and quotes from yfinance."

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbol",
            help="Only sync this symbol (otherwise syncs all tickers).",
        )

    def handle(self, *args, **options):
        symbol = options.get("symbol")
        qs = Ticker.objects.all()
        if symbol:
            qs = qs.filter(symbol=symbol.upper())
            if not qs.exists():
                raise CommandError(f"Ticker {symbol} not found.")

        for ticker in qs:
            self.stdout.write(f"Syncing {ticker.symbol}...")
            try:
                result = sync_service.sync_ticker(ticker)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {ticker.symbol}: +{result.new_dividends} dividends"
                        f"{', price=' + str(result.price) if result.price else ''}"
                    )
                )
            except YFinanceError as exc:
                self.stdout.write(self.style.ERROR(f"  {ticker.symbol}: {exc}"))
