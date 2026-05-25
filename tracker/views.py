from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DividendForm, HoldingForm, TickerForm, TickerQuickAddForm
from .models import Dividend, Holding, Ticker
from .services import sync as sync_service
from .services.projections import monthly_projection
from .services.yfinance_client import YFinanceError


def dashboard(request):
    holdings = Holding.objects.select_related("ticker", "ticker__quote").all()

    total_market_value = Decimal("0")
    total_annual_income = Decimal("0")
    has_market_value = False
    for h in holdings:
        mv = h.market_value
        if mv is not None:
            total_market_value += mv
            has_market_value = True
        total_annual_income += h.annual_income

    avg_yield = None
    if has_market_value and total_market_value > 0:
        avg_yield = (total_annual_income / total_market_value) * Decimal("100")

    projection = monthly_projection(holdings, months=12)

    context = {
        "holdings": holdings,
        "total_market_value": total_market_value if has_market_value else None,
        "total_annual_income": total_annual_income,
        "avg_yield": avg_yield,
        "projection": projection,
        "projection_labels": [p.label for p in projection],
        "projection_values": [float(p.amount) for p in projection],
    }
    return render(request, "tracker/dashboard.html", context)


def ticker_list(request):
    tickers = Ticker.objects.all().prefetch_related("dividends", "holdings")
    return render(request, "tracker/ticker_list.html", {"tickers": tickers})


def ticker_add(request):
    quick_form = TickerQuickAddForm(request.POST or None)
    manual_form = TickerForm()
    if request.method == "POST" and quick_form.is_valid():
        symbol = quick_form.cleaned_data["symbol"]
        if Ticker.objects.filter(symbol=symbol).exists():
            messages.warning(request, f"{symbol} 는 이미 등록되어 있습니다.")
            return redirect("ticker_detail", symbol=symbol)
        ticker = Ticker.objects.create(symbol=symbol)
        try:
            result = sync_service.sync_ticker(ticker)
            messages.success(
                request,
                f"{ticker.symbol} 추가됨. 배당 {result.new_dividends}건 동기화.",
            )
        except YFinanceError as exc:
            messages.error(
                request,
                f"{symbol} 자동 수집 실패: {exc}. 수동으로 메타데이터를 입력해 주세요.",
            )
        return redirect("ticker_detail", symbol=ticker.symbol)
    return render(
        request,
        "tracker/ticker_add.html",
        {"quick_form": quick_form, "manual_form": manual_form},
    )


def ticker_manual_create(request):
    if request.method != "POST":
        return redirect("ticker_add")
    form = TickerForm(request.POST)
    if form.is_valid():
        ticker = form.save()
        messages.success(request, f"{ticker.symbol} 수동 등록 완료.")
        return redirect("ticker_detail", symbol=ticker.symbol)
    return render(
        request,
        "tracker/ticker_add.html",
        {"quick_form": TickerQuickAddForm(), "manual_form": form},
    )


def ticker_detail(request, symbol):
    ticker = get_object_or_404(Ticker, symbol=symbol.upper())
    dividends = ticker.dividends.all()[:50]
    holdings = ticker.holdings.all()
    return render(
        request,
        "tracker/ticker_detail.html",
        {"ticker": ticker, "dividends": dividends, "holdings": holdings},
    )


@require_POST
def ticker_sync(request, symbol):
    ticker = get_object_or_404(Ticker, symbol=symbol.upper())
    try:
        result = sync_service.sync_ticker(ticker)
        messages.success(
            request,
            f"{ticker.symbol} 동기화 완료. 신규 배당 {result.new_dividends}건.",
        )
    except YFinanceError as exc:
        messages.error(request, f"{ticker.symbol} 동기화 실패: {exc}")

    if getattr(request, "htmx", False):
        return render(
            request,
            "tracker/partials/ticker_sync_status.html",
            {"ticker": ticker},
        )
    return redirect("ticker_detail", symbol=ticker.symbol)


def ticker_delete(request, symbol):
    ticker = get_object_or_404(Ticker, symbol=symbol.upper())
    if request.method == "POST":
        ticker.delete()
        messages.success(request, f"{symbol} 삭제됨.")
        return redirect("ticker_list")
    return render(request, "tracker/ticker_confirm_delete.html", {"ticker": ticker})


def holding_list(request):
    holdings = Holding.objects.select_related("ticker", "ticker__quote").all()
    return render(request, "tracker/holding_list.html", {"holdings": holdings})


def holding_add(request):
    form = HoldingForm(request.POST or None)
    if form.is_valid():
        h = form.save()
        messages.success(request, f"{h.ticker.symbol} 보유 등록.")
        return redirect("holding_list")
    return render(request, "tracker/holding_form.html", {"form": form, "title": "보유 추가"})


def holding_edit(request, pk):
    holding = get_object_or_404(Holding, pk=pk)
    form = HoldingForm(request.POST or None, instance=holding)
    if form.is_valid():
        form.save()
        messages.success(request, "보유 정보 갱신.")
        return redirect("holding_list")
    return render(request, "tracker/holding_form.html", {"form": form, "title": "보유 수정"})


@require_POST
def holding_delete(request, pk):
    holding = get_object_or_404(Holding, pk=pk)
    holding.delete()
    messages.success(request, "보유 삭제됨.")
    return redirect("holding_list")


def dividend_list(request):
    qs = Dividend.objects.select_related("ticker")
    symbol = request.GET.get("symbol")
    source = request.GET.get("source")
    if symbol:
        qs = qs.filter(ticker__symbol=symbol.upper())
    if source:
        qs = qs.filter(source=source)
    dividends = qs[:200]
    return render(
        request,
        "tracker/dividend_list.html",
        {
            "dividends": dividends,
            "symbol": symbol or "",
            "source": source or "",
            "tickers": Ticker.objects.all(),
        },
    )


def dividend_add(request):
    form = DividendForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "배당 기록 추가됨.")
        return redirect("dividend_list")
    return render(request, "tracker/dividend_form.html", {"form": form})


def projection_view(request):
    holdings = Holding.objects.select_related("ticker").all()
    projection = monthly_projection(holdings, months=12)
    total = sum((p.amount for p in projection), Decimal("0"))
    return render(
        request,
        "tracker/projection.html",
        {
            "projection": projection,
            "total": total,
            "labels": [p.label for p in projection],
            "values": [float(p.amount) for p in projection],
        },
    )
