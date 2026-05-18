
import json
import pandas as pd
import requests
from decimal import Decimal
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CurrencyPair, PriceData, Trade, DerivAccount
from .deriv_client import deriv_client
import talib
import numpy as np
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_currency_pairs(request):
    """Get all available currency pairs"""
    pairs = CurrencyPair.objects.filter(is_active=True)
    data = [{'id': p.id, 'symbol': p.symbol, 'name': p.name} for p in pairs]
    return Response(data)

@api_view(['GET'])
def get_live_prices(request):
    """Get current prices for all active currency pairs"""
    pairs = CurrencyPair.objects.filter(is_active=True)
    prices = []
    
    for pair in pairs:
        latest_price = PriceData.objects.filter(currency_pair=pair).first()
        if latest_price:
            prices.append({
                'symbol': pair.symbol,
                'bid': float(latest_price.bid_price),
                'ask': float(latest_price.ask_price),
                'spread': float(latest_price.ask_price - latest_price.bid_price),
                'timestamp': latest_price.timestamp.isoformat()
            })
    
    return Response(prices)

@api_view(['GET'])
def get_price_history(request, symbol):
    """Get historical price data for technical analysis"""
    try:
        pair = CurrencyPair.objects.get(symbol=symbol)
        prices = PriceData.objects.filter(currency_pair=pair)[:100]
        
        data = []
        for price in reversed(prices):
            data.append({
                'timestamp': price.timestamp.isoformat(),
                'bid': float(price.bid_price),
                'ask': float(price.ask_price),
                'close': float((price.bid_price + price.ask_price) / 2)
            })
        
        return Response(data)
    except CurrencyPair.DoesNotExist:
        return Response({'error': 'Currency pair not found'}, status=404)

@api_view(['GET'])
def get_technical_analysis(request, symbol):
    """Calculate technical indicators using real Deriv data"""
    try:
        pair = CurrencyPair.objects.get(symbol=symbol)
        prices = PriceData.objects.filter(currency_pair=pair)[:50]
        
        if len(prices) < 20:
            return Response({'error': 'Insufficient data for analysis'}, status=400)
        
        # Convert to arrays for TA-Lib
        closes = np.array([float((p.bid_price + p.ask_price) / 2) for p in reversed(prices)])
        
        # Calculate indicators
        sma_20 = talib.SMA(closes, timeperiod=20)
        rsi = talib.RSI(closes, timeperiod=14)
        macd, macd_signal, macd_hist = talib.MACD(closes)
        
        # Determine trend
        current_price = closes[-1]
        sma_current = sma_20[-1] if not np.isnan(sma_20[-1]) else current_price
        
        if current_price > sma_current * 1.001:  # 0.1% above SMA
            trend = 'BULLISH'
        elif current_price < sma_current * 0.999:  # 0.1% below SMA  
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        analysis = {
            'symbol': symbol,
            'current_price': float(current_price),
            'sma_20': float(sma_20[-1]) if not np.isnan(sma_20[-1]) else None,
            'rsi': float(rsi[-1]) if not np.isnan(rsi[-1]) else None,
            'macd': float(macd[-1]) if not np.isnan(macd[-1]) else None,
            'macd_signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None,
            'trend': trend,
            'data_source': 'Deriv API'
        }
        
        return Response(analysis)
    except CurrencyPair.DoesNotExist:
        return Response({'error': 'Currency pair not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def place_trade(request):
    """Place a new trade using Deriv API"""
    try:
        data = request.data
        pair = CurrencyPair.objects.get(symbol=data['symbol'])
        
        # Get current price from our database
        latest_price = PriceData.objects.filter(currency_pair=pair).first()
        if not latest_price:
            return Response({'error': 'No price data available'}, status=400)
        
        # Determine entry price
        entry_price = latest_price.ask_price if data['trade_type'] == 'BUY' else latest_price.bid_price
        
        # Create trade record
        trade = Trade.objects.create(
            currency_pair=pair,
            trade_type=data['trade_type'],
            entry_price=entry_price,
            quantity=Decimal(data['quantity']),
            stop_loss=Decimal(data.get('stop_loss', 0)) if data.get('stop_loss') else None,
            take_profit=Decimal(data.get('take_profit', 0)) if data.get('take_profit') else None
        )
        
        # Place order through Deriv API
        if deriv_client.is_connected:
            result = deriv_client.place_trade_order(
                symbol=data['symbol'],
                trade_type=data['trade_type'],
                amount=float(data['quantity']),
                stop_loss=float(data.get('stop_loss', 0)) if data.get('stop_loss') else None,
                take_profit=float(data.get('take_profit', 0)) if data.get('take_profit') else None
            )
            
            if result.get('success'):
                logger.info(f"Trade placed through Deriv API: {trade.id}")
            else:
                logger.error(f"Deriv API error: {result.get('error')}")
        else:
            logger.warning("Deriv API not connected, trade placed locally only")
        
        return Response({
            'trade_id': trade.id,
            'message': f"{data['trade_type']} order placed successfully",
            'entry_price': float(trade.entry_price),
            'deriv_connected': deriv_client.is_connected
        })
        
    except CurrencyPair.DoesNotExist:
        return Response({'error': 'Currency pair not found'}, status=404)
    except Exception as e:
        logger.error(f"Error placing trade: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def close_trade(request, trade_id):
    """Close an open trade"""
    try:
        trade = get_object_or_404(Trade, id=trade_id, status='OPEN')
        
        # Get current price
        latest_price = PriceData.objects.filter(currency_pair=trade.currency_pair).first()
        if not latest_price:
            return Response({'error': 'No price data available'}, status=400)
        
        # Determine exit price
        exit_price = latest_price.bid_price if trade.trade_type == 'BUY' else latest_price.ask_price
        
        # Calculate profit/loss
        if trade.trade_type == 'BUY':
            profit_loss = (exit_price - trade.entry_price) * trade.quantity
        else:
            profit_loss = (trade.entry_price - exit_price) * trade.quantity
        
        # Close through Deriv API if connected
        if deriv_client.is_connected and trade.deriv_contract_id:
            deriv_client.close_position(trade.deriv_contract_id)
        
        # Update trade
        trade.exit_price = exit_price
        trade.profit_loss = profit_loss
        trade.status = 'CLOSED'
        trade.closed_at = timezone.now()
        trade.save()
        
        return Response({
            'message': 'Trade closed successfully',
            'exit_price': float(exit_price),
            'profit_loss': float(profit_loss),
            'deriv_connected': deriv_client.is_connected
        })
        
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_trades(request):
    """Get all trades"""
    trades = Trade.objects.all()
    data = []
    
    for trade in trades:
        data.append({
            'id': trade.id,
            'symbol': trade.currency_pair.symbol,
            'trade_type': trade.trade_type,
            'status': trade.status,
            'entry_price': float(trade.entry_price),
            'exit_price': float(trade.exit_price) if trade.exit_price else None,
            'quantity': float(trade.quantity),
            'profit_loss': float(trade.profit_loss) if trade.profit_loss else None,
            'opened_at': trade.opened_at.isoformat(),
            'closed_at': trade.closed_at.isoformat() if trade.closed_at else None,
            'deriv_contract_id': trade.deriv_contract_id
        })
    
    return Response(data)

@api_view(['GET'])
def get_portfolio_summary(request):
    """Get portfolio summary"""
    open_trades = Trade.objects.filter(status='OPEN')
    closed_trades = Trade.objects.filter(status='CLOSED')
    
    total_profit_loss = sum([float(t.profit_loss) for t in closed_trades if t.profit_loss])
    open_positions = len(open_trades)
    total_trades = Trade.objects.count()
    
    # Calculate win rate
    winning_trades = closed_trades.filter(profit_loss__gt=0).count()
    win_rate = (winning_trades / len(closed_trades)) if closed_trades else 0
    
    return Response({
        'total_profit_loss': total_profit_loss,
        'open_positions': open_positions,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'deriv_connected': deriv_client.is_connected
    })

@api_view(['GET'])
def get_deriv_status(request):
    """Get Deriv API connection status"""
    return Response({
        'connected': deriv_client.is_connected,
        'api_url': deriv_client.ws.url if deriv_client.ws else None,
        'subscriptions': len(deriv_client.subscriptions),
        'supported_pairs': list(deriv_client.forex_symbols.keys())
    })

@api_view(['GET'])
def get_account_info(request):
    """Get Deriv account information"""
    try:
        if deriv_client.is_connected:
            deriv_client.get_account_balance()
            deriv_client.get_portfolio()
            
        # Get from database
        accounts = DerivAccount.objects.all()
        account_data = []
        
        for account in accounts:
            account_data.append({
                'account_id': account.account_id,
                'currency': account.currency,
                'balance': float(account.balance),
                'is_demo': account.is_demo,
                'last_updated': account.last_updated.isoformat()
            })
        
        return Response({
            'accounts': account_data,
            'deriv_connected': deriv_client.is_connected
        })
        
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return Response({'error': str(e)}, status=500)