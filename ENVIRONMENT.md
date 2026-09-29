"""Environment variables required in production.

When DEBUG is off, backend/settings.py refuses to start unless SECRET_KEY,
DJANGO_ALLOWED_HOSTS, DATABASE_URL and a live PAYSTACK_SECRET_KEY are all
present. This is the same list, kept in one place to make deployment setup
unambiguous.

Required:
    SECRET_KEY           python -c "import secrets; print(secrets.token_urlsafe(64))"
    DJANGO_ALLOWED_HOSTS comma-separated hostnames, e.g. api.example.com
    DATABASE_URL         postgres://user:pass@host:5432/dbname
    PAYSTACK_SECRET_KEY  live secret (sk_live_...); test keys are rejected

Strongly recommended:
    CORS_ALLOWED_ORIGINS comma-separated frontend origins, e.g. https://app.example.com
    FRONTEND_URL         used to build password-reset and invite links
    EMAIL_HOST / EMAIL_USER / EMAIL_PASSWORD / EMAIL_GENERAL
    DERIV_API_TOKEN / DERIV_APP_ID
    THROTTLE_ANON        e.g. 60/hour
    THROTTLE_USER        e.g. 600/hour

Optional:
    SECURE_SSL_REDIRECT  set to false only behind a TLS-terminating proxy
    SECURE_HSTS_SECONDS  defaults to 31536000

Never set DEBUG=True in production.
"""
