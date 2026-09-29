from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .authentication import BearerTokenAuthentication
from .models import StrategyConfig
from .permissions import ReadOnlyOrAdmin

# Bounds for the live-trading knobs. Anything outside these is a mistake or an
# attempt to blow up the account, and is rejected rather than silently clamped.
MAX_RISK_PER_TRADE = 0.05
MAX_LOTS = 100.0


def _get_strategy():
    config, _ = StrategyConfig.objects.get_or_create(id=1)
    return config


def _serialize(config):
    return {
        'strategy': config.strategy,
        'pairs': config.pairs or [],
        'risk': {
            'riskPerTrade': float(config.risk_per_trade),
            'maxLots': float(config.max_lots),
        },
    }


@api_view(['GET', 'PUT'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([ReadOnlyOrAdmin])
def strategy(request):
    config = _get_strategy()

    if request.method == 'GET':
        return Response(_serialize(config))

    data = request.data or {}
    if 'strategy' in data and isinstance(data['strategy'], str):
        config.strategy = data['strategy'][:64]
    if 'pairs' in data and isinstance(data['pairs'], list):
        config.pairs = [str(p)[:16] for p in data['pairs']][:50]

    risk = data.get('risk') or {}
    if 'riskPerTrade' in risk:
        try:
            value = float(risk['riskPerTrade'])
        except (TypeError, ValueError):
            value = None
        if value is not None and 0 < value <= MAX_RISK_PER_TRADE:
            config.risk_per_trade = value
    if 'maxLots' in risk:
        try:
            value = float(risk['maxLots'])
        except (TypeError, ValueError):
            value = None
        if value is not None and 0 < value <= MAX_LOTS:
            config.max_lots = value

    config.save()
    return Response(_serialize(config))
