from collections import defaultdict
from decimal import Decimal
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .authentication import BearerTokenAuthentication
from .models import EquityPoint, PriceData, Trade


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def analytics_summary(request):
    """Aggregate performance stats for the data analysis dashboard."""
    closed = list(Trade.objects.filter(status='CLOSED'))
    open_trades = Trade.objects.filter(status='OPEN')

    total_pnl = sum((t.profit_loss or 0) for t in closed)
    wins = [t for t in closed if (t.profit_loss or 0) > 0]
    win_rate = (len(wins) / len(closed)) if closed else 0.0

    # P&L by pair
    by_pair = defaultdict(lambda: {'pnl': Decimal('0'), 'trades': 0, 'wins': 0})
    for t in closed:
        symbol = t.currency_pair.symbol
        by_pair[symbol]['pnl'] += t.profit_loss or 0
        by_pair[symbol]['trades'] += 1
        if (t.profit_loss or 0) > 0:
            by_pair[symbol]['wins'] += 1

    profit_by_pair = []
    for symbol, agg in by_pair.items():
        profit_by_pair.append(
            {
                'pair': symbol,
                'pnl': float(agg['pnl']),
                'trades': agg['trades'],
                'winRate': round(agg['wins'] / agg['trades'], 4) if agg['trades'] else 0,
            }
        )
    profit_by_pair.sort(key=lambda p: p['pnl'], reverse=True)

    # Daily P&L buckets for a bar/line view
    daily = defaultdict(lambda: Decimal('0'))
    for t in closed:
        day = t.closed_at.date().isoformat() if t.closed_at else None
        if day:
            daily[day] += t.profit_loss or 0
    daily_pnl = [{'date': d, 'pnl': float(v)} for d, v in sorted(daily.items())]

    equity = [
        {'timestamp': p.timestamp.isoformat(), 'value': float(p.value)}
        for p in EquityPoint.objects.all()[:500]
    ]

    return Response(
        {
            'totalTrades': Trade.objects.count(),
            'closedTrades': len(closed),
            'openPositions': open_trades.count(),
            'totalPnl': float(total_pnl),
            'winRate': round(win_rate, 4),
            'profitByPair': profit_by_pair,
            'dailyPnl': daily_pnl,
            'equity': equity,
        }
    )


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def analytics_trades(request):
    """Return recent trades (for per-trade analysis/list)."""
    try:
        limit = int(request.query_params.get('limit', 50))
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 200))

    trades = Trade.objects.all()[:limit]
    data = []
    for t in trades:
        data.append(
            {
                'id': t.id,
                'symbol': t.currency_pair.symbol,
                'type': t.trade_type,
                'status': t.status,
                'lots': float(t.quantity),
                'entry': float(t.entry_price),
                'exit': float(t.exit_price) if t.exit_price is not None else None,
                'profit': float(t.profit_loss) if t.profit_loss is not None else None,
                'openedAt': t.opened_at.isoformat(),
                'closedAt': t.closed_at.isoformat() if t.closed_at else None,
            }
        )
    return Response(data)
