from django.urls import path
from . import views

urlpatterns = [
    path('currency-pairs/', views.get_currency_pairs, name='currency-pairs'),
    path('live-prices/', views.get_live_prices, name='live-prices'),
    path('price-history/<str:symbol>/', views.get_price_history, name='price-history'),
    path('technical-analysis/<str:symbol>/', views.get_technical_analysis, name='technical-analysis'),
    path('place-trade/', views.place_trade, name='place-trade'),
    path('close-trade/<int:trade_id>/', views.close_trade, name='close-trade'),
    path('trades/', views.get_trades, name='trades'),
    path('portfolio/', views.get_portfolio_summary, name='portfolio'),
    path('deriv-status/', views.get_deriv_status, name='deriv-status'),
    path('account-info/', views.get_account_info, name='account-info'),
]