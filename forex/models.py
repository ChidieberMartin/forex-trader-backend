from django.db import models

# Create your models here.
from django.utils import timezone

class CurrencyPair(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    deriv_symbol = models.CharField(max_length=20, blank=True, null=True)  # Deriv's symbol format
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symbol

class PriceData(models.Model):
    currency_pair = models.ForeignKey(CurrencyPair, on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=12, decimal_places=6)
    ask_price = models.DecimalField(max_digits=12, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['currency_pair', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.currency_pair.symbol} - {self.bid_price}/{self.ask_price}"

class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('PENDING', 'Pending'),
    ]

    currency_pair = models.ForeignKey(CurrencyPair, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    entry_price = models.DecimalField(max_digits=12, decimal_places=6)
    exit_price = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Deriv-specific fields
    deriv_contract_id = models.CharField(max_length=50, blank=True, null=True)
    deriv_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['status', '-opened_at']),
            models.Index(fields=['currency_pair', '-opened_at']),
        ]

    def __str__(self):
        return f"{self.trade_type} {self.currency_pair.symbol} - {self.status}"

class DerivAccount(models.Model):
    """Store Deriv account information"""
    account_id = models.CharField(max_length=50, unique=True)
    currency = models.CharField(max_length=10, default='USD')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_demo = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deriv Account: {self.account_id}"