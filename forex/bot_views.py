from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .authentication import BearerTokenAuthentication
from .models import BotState, EquityPoint, PriceData, Trade
from .permissions import IsAdminUser


def _get_bot_state():
    state, _ = BotState.objects.get_or_create(id=1)
    return state


def _current_price(pair):
    latest = PriceData.objects.filter(currency_pair=pair).first()
    return latest


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_bot_status(request):
    state = _get_bot_state()
    return Response({'running': state.running})


@api_view(['POST'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUser])
def start_bot(request):
    state = _get_bot_state()
    state.running = True
    state.save()
    return Response({'running': state.running, 'message': 'Bot started.'})


@api_view(['POST'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUser])
def stop_bot(request):
    state = _get_bot_state()
    state.running = False
    state.save()
    return Response({'running': state.running, 'message': 'Bot stopped.'})


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_equity(request):
    """Return equity curve points as [{ timestamp, value }]."""
    points = EquityPoint.objects.all()[:500]
    data = [
        {'timestamp': p.timestamp.isoformat(), 'value': float(p.value)}
        for p in points
    ]
    return Response(data)


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_positions(request):
    """Return open positions shaped as [{ symbol, type, lots, entry, current, profit }]."""
    open_trades = Trade.objects.filter(status='OPEN')
    data = []
    for trade in open_trades:
        current = trade.entry_price
        latest = _current_price(trade.currency_pair)
        if latest:
            current = (
                latest.bid_price if trade.trade_type == 'SELL' else latest.ask_price
            )
        if trade.trade_type == 'BUY':
            profit = (current - trade.entry_price) * trade.quantity
        else:
            profit = (trade.entry_price - current) * trade.quantity
        data.append({
            'symbol': trade.currency_pair.symbol,
            'type': trade.trade_type,
            'lots': float(trade.quantity),
            'entry': float(trade.entry_price),
            'current': float(current),
            'profit': float(profit),
        })
    return Response(data)


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_bot_trades(request):
    """Return recent fills shaped as [{ id, symbol, type, lots, price, profit, time }]."""
    try:
        limit = int(request.query_params.get('limit', 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 200))

    trades = Trade.objects.all()[:limit]
    data = []
    for trade in trades:
        profit = trade.profit_loss
        if profit is None:
            if trade.trade_type == 'BUY':
                profit = (trade.exit_price or trade.entry_price) - trade.entry_price
            else:
                profit = trade.entry_price - (trade.exit_price or trade.entry_price)
            profit = profit * trade.quantity
        data.append({
            'id': trade.id,
            'symbol': trade.currency_pair.symbol,
            'type': trade.trade_type,
            'lots': float(trade.quantity),
            'price': float(trade.exit_price if trade.exit_price is not None else trade.entry_price),
            'profit': float(profit),
            'time': trade.opened_at.isoformat(),
        })
    return Response(data)
