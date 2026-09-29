import os
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .authentication import BearerTokenAuthentication
from .models import Profile, Referral
from .referral import ensure_referral_code, REFERRER_REWARD, REFEREE_REWARD

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


@api_view(['GET'])
@authentication_classes([BearerTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_referrals(request):
    """Return the authenticated user's referral code, link, rewards and history."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    code = ensure_referral_code(profile)

    referred = Referral.objects.filter(referrer=request.user).select_related('referee')

    return Response(
        {
            'code': code,
            'referralLink': f"{FRONTEND_URL}/signup?ref={code}",
            'rewardBalance': float(profile.reward_balance),
            'referrerReward': float(REFERRER_REWARD),
            'refereeReward': float(REFEREE_REWARD),
            'referralCount': referred.count(),
            'referred': [
                {
                    'name': r.referee.first_name or r.referee.username,
                    'email': r.referee.email,
                    'reward': float(r.referrer_reward),
                    'createdAt': r.created_at.isoformat(),
                }
                for r in referred
            ],
        }
    )
