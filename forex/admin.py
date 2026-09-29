from django.contrib import admin
from .models import (
    CurrencyPair,
    PriceData,
    Trade,
    DerivAccount,
    PasswordResetToken,
    BotState,
    StrategyConfig,
    EquityPoint,
    Profile,
    AuditLog,
    FraudResult,
    Referral,
    Invite,
    IdentityVerification,
    Withdrawal,
)


@admin.register(CurrencyPair)
class CurrencyPairAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'is_active')
    list_filter = ('is_active',)


@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = ('currency_pair', 'bid_price', 'ask_price', 'timestamp')


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('currency_pair', 'trade_type', 'status', 'quantity', 'profit_loss', 'opened_at')
    list_filter = ('status', 'trade_type')


@admin.register(DerivAccount)
class DerivAccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'currency', 'balance', 'is_demo')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'used')


@admin.register(BotState)
class BotStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'running', 'updated_at')


@admin.register(StrategyConfig)
class StrategyConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'strategy', 'risk_per_trade', 'max_lots', 'updated_at')


@admin.register(EquityPoint)
class EquityPointAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'value')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'status', 'account_type', 'created_at')
    list_filter = ('role', 'status', 'account_type')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'target')


@admin.register(FraudResult)
class FraudResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'level', 'updated_at')
    list_filter = ('level',)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referee', 'code', 'referrer_reward', 'referee_reward', 'created_at')


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'accepted', 'created_at')
    list_filter = ('accepted',)


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'doc_type',
        'doc_number',
        'status',
        'submitted_at',
        'reviewed_at',
    )
    list_filter = ('status', 'doc_type')


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'amount',
        'fee',
        'net_amount',
        'status',
        'created_at',
    )
    list_filter = ('status',)
