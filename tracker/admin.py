from django.contrib import admin

from .models import Dividend, Holding, Quote, Ticker


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "currency", "dividend_frequency", "last_synced_at")
    search_fields = ("symbol", "name")
    list_filter = ("dividend_frequency", "currency")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("ticker", "shares", "average_cost", "acquired_at")
    search_fields = ("ticker__symbol",)


@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ("ticker", "ex_date", "pay_date", "amount_per_share", "source")
    list_filter = ("source", "ticker")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "ex_date"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("ticker", "price", "fetched_at")
