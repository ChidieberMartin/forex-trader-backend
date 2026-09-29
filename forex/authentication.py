from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """Token authentication that accepts the `Authorization: Bearer <token>`
    header, matching the frontend API client."""
    keyword = 'Bearer'
