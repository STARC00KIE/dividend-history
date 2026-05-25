from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tickers/", views.ticker_list, name="ticker_list"),
    path("tickers/add/", views.ticker_add, name="ticker_add"),
    path("tickers/add/manual/", views.ticker_manual_create, name="ticker_manual_create"),
    path("tickers/<str:symbol>/", views.ticker_detail, name="ticker_detail"),
    path("tickers/<str:symbol>/sync/", views.ticker_sync, name="ticker_sync"),
    path("tickers/<str:symbol>/delete/", views.ticker_delete, name="ticker_delete"),
    path("holdings/", views.holding_list, name="holding_list"),
    path("holdings/add/", views.holding_add, name="holding_add"),
    path("holdings/<int:pk>/edit/", views.holding_edit, name="holding_edit"),
    path("holdings/<int:pk>/delete/", views.holding_delete, name="holding_delete"),
    path("dividends/", views.dividend_list, name="dividend_list"),
    path("dividends/add/", views.dividend_add, name="dividend_add"),
    path("projections/", views.projection_view, name="projection_view"),
]
