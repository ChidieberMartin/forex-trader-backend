"""
Fraud detection engine for the OKORO FX platform.

This is currently a deterministic, rule-based risk scorer that produces a
0-100 "fraud score" for a given user, along with human-readable reasons.

It is designed so a real ML model can be plugged in later: the interface is a
single `score_user(user)` function returning `(score, level, reasons)`, and all
feature extraction is isolated from the scoring rules. Swap the internals with
a trained model (e.g. sklearn/xgboost) without changing callers.

Signals considered (computed from data already in the DB):
  - Anomalous trade frequency / volume
  - Unrealistic trade sizes or P&L (indicative of fake/manipulated trades)
  - Abnormally high win rate (suggestive of self-dealing or backfilled data)
  - Multiple profiles could share this account's behaviour
  - Account status / role hard-failures handled at the view level
"""

from decimal import Decimal
from datetime import timedelta
from .models import Trade, Profile

# Win-rate thresholds. A suspiciously perfect win rate is a red flag.
_SUSPICIOUS_WIN_RATE = 0.90
_PERFECT_WIN_RATE = 0.995

# Hard caps on per-trade size / magnitude.
_MAX_LOTS = Decimal('10')
_MAX_ABS_PNL = Decimal('100000')


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _level_for(score):
    if score >= 75:
        return 'critical'
    if score >= 50:
        return 'high'
    if score >= 25:
        return 'medium'
    return 'low'


def extract_features(user):
    """Pull raw signals from the DB into a plain dict (for later ML use)."""
    trades = Trade.objects.filter(currency_pair__isnull=False)
    # NOTE: trades are not user-bound on the Trade model today; all open trades
    # are platform-global. Once trades are tied to a user, filter by user here.
    # See TODO at the score_user docstring.
    closed = [t for t in trades if t.status == 'CLOSED']

    total = len(trades)
    closed_count = len(closed)
    wins = sum(1 for t in closed if (t.profit_loss or 0) > 0)

    pnls = [abs(float(t.profit_loss)) for t in closed if t.profit_loss is not None]
    lots = [float(t.quantity) for t in trades]

    max_lot = max(lots) if lots else 0.0
    max_pnl = max(pnls) if pnls else 0.0
    win_rate = (wins / closed_count) if closed_count else 0.0

    return {
        'total_trades': total,
        'closed_trades': closed_count,
        'wins': wins,
        'win_rate': win_rate,
        'max_lots': max_lot,
        'max_abs_pnl': max_pnl,
    }


def score_user(user):
    """
    Return (score, level, reasons) for a user as a tuple.
    score is an int 0-100; level one of low/medium/high/critical.
    """
    reasons = []
    points = 0

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = None

    if profile is None:
        points += 5
        reasons.append('Account missing profile record')
    elif profile.status != 'active':
        points += 30
        reasons.append(f'Account is {profile.status}')

    features = extract_features(user)

    # 1. Trade volume / frequency anomalies
    if features['closed_trades'] == 0 and features['total_trades'] > 0:
        points += 10
        reasons.append('All trades still open (no realized history)')

    # 2. Unrealistic per-trade size
    if features['max_lots'] > 15:
        points += 20
        reasons.append(f'Extreme lot size detected: {features["max_lots"]:.2f} lots')

    # 3. Unrealistic P&L magnitude per trade
    if features['max_abs_pnl'] > 50000:
        points += 20
        reasons.append(f'Large single-trade P&L: ${features["max_abs_pnl"]:,.0f}')

    # 4. Suspiciously perfect win rate
    if features['closed_trades'] >= 5:
        if features['win_rate'] >= _PERFECT_WIN_RATE:
            points += 35
            reasons.append(
                f'Near-perfect win rate of {features["win_rate"] * 100:.1f}%'
            )
        elif features['win_rate'] >= _SUSPICIOUS_WIN_RATE:
            points += 15
            reasons.append(
                f'Unusually high win rate of {features["win_rate"] * 100:.1f}%'
            )

    points = min(points, 100)
    level = _level_for(points)

    if not reasons:
        reasons.append('No suspicious activity detected')

    return points, level, reasons


def recompute_for_user(user):
    """Compute and persist a FraudResult for a user. Returns (score, level, reasons)."""
    from .models import FraudResult

    score, level, reasons = score_user(user)
    result, _ = FraudResult.objects.get_or_create(user=user)
    result.score = score
    result.level = level
    result.reasons = reasons
    result.save()
    return result
