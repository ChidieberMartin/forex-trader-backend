from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminUser(BasePermission):
    """Allows access only to users whose Profile role is 'admin'."""

    message = 'Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, 'profile', None)
        return profile is not None and profile.role == 'admin'


class ReadOnlyOrAdmin(IsAdminUser):
    """Lets anyone read, but restricts writes to admins.

    Used for endpoints that serve public-ish config while the write side
    mutates global trading state.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().has_permission(request, view)
