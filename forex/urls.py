from django.urls import path
from . import views
from . import auth_views, bot_views, strategy_views, admin_views, analytics_views, referral_views, account_views

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

    # Auth
    path('auth/login/', auth_views.login, name='auth-login'),
    path('auth/signup/', auth_views.signup, name='auth-signup'),
    path('auth/forgot-password/', auth_views.forgot_password, name='auth-forgot-password'),
    path('auth/reset-password/', auth_views.reset_password, name='auth-reset-password'),
    path('auth/me/', auth_views.me, name='auth-me'),
    path('auth/invite/', auth_views.invite_user, name='auth-invite'),
    path('auth/accept-invite/', auth_views.accept_invite, name='auth-accept-invite'),
    path('auth/change-password/', auth_views.change_password, name='auth-change-password'),

    # Bot
    path('bot/status/', bot_views.get_bot_status, name='bot-status'),
    path('bot/start/', bot_views.start_bot, name='bot-start'),
    path('bot/stop/', bot_views.stop_bot, name='bot-stop'),
    path('bot/equity/', bot_views.get_equity, name='bot-equity'),
    path('bot/positions/', bot_views.get_positions, name='bot-positions'),
    path('bot/trades/', bot_views.get_bot_trades, name='bot-trades'),

    # Strategy
    path('strategy/', strategy_views.strategy, name='strategy'),

    # Admin
    path('admin/users/', admin_views.list_users, name='admin-users'),
    path('admin/users/<int:user_id>/status/', admin_views.change_user_status, name='admin-user-status'),
    path('admin/users/<int:user_id>/role/', admin_views.change_user_role, name='admin-user-role'),
    path('admin/users/<int:user_id>/fraud/', admin_views.recompute_fraud, name='admin-user-fraud'),
    path('admin/audit-logs/', admin_views.list_audit_logs, name='admin-audit-logs'),

    # Fraud
    path('fraud/users/', admin_views.fraud_scores, name='fraud-users'),

    # Analytics
    path('analytics/summary/', analytics_views.analytics_summary, name='analytics-summary'),
    path('analytics/trades/', analytics_views.analytics_trades, name='analytics-trades'),

    # Referrals
    path('referrals/', referral_views.get_referrals, name='referrals'),

    # Account / KYC / Live funding
    path('account/', account_views.account_status, name='account-status'),
    path('account/type/', account_views.set_account_type, name='account-type'),
    path('account/kyc/', account_views.submit_kyc, name='account-kyc'),
    path('account/live/fund/', account_views.live_fund, name='account-live-fund'),
    path('account/withdrawals/', account_views.list_withdrawals, name='account-withdrawals'),
    path('account/withdraw/', account_views.create_withdrawal, name='account-withdraw'),
    path('paystack/webhook/', account_views.paystack_webhook, name='paystack-webhook'),

    # Admin KYC
    path('admin/kyc/', admin_views.list_kyc, name='admin-kyc'),
    path('admin/kyc/<int:verification_id>/review/', admin_views.review_kyc, name='admin-kyc-review'),

    # Admin Withdrawals
    path('admin/withdrawals/', admin_views.list_withdrawals_admin, name='admin-withdrawals'),
    path('admin/withdrawals/<int:withdrawal_id>/review/', admin_views.review_withdrawal, name='admin-withdrawal-review'),
]