import os
from api.configuraciones_api.helpers import get_conf


def _fetch(key: str, default=None):
    """Read from environment or database configuration."""
    value = os.getenv(key)
    if value is not None:
        return value
    try:
        return get_conf(key, os.getenv("DJANGO_ENV", "production"))
    except Exception:
        return default


def load_env() -> dict:
    settings = {
        "REDIRECT_URI": _fetch("REDIRECT_URI"),
        "CLIENT_ID": _fetch("CLIENT_ID"),
        "CLIENT_SECRET": _fetch("CLIENT_SECRET"),
        "ORIGIN": _fetch("ORIGIN"),
        "TOKEN_URL": _fetch("TOKEN_URL"),
        "OTP_URL": _fetch("OTP_URL"),
        "AUTH_URL": _fetch("AUTH_URL"),
        "API_URL": _fetch("API_URL"),
        "AUTHORIZE_URL": _fetch("AUTHORIZE_URL"),
        "SCOPE": _fetch("SCOPE"),
        "ACCESS_TOKEN": _fetch("ACCESS_TOKEN"),
        "TIMEOUT": int(_fetch("TIMEOUT", 600)),
        "TIMEOUT_REQUEST": int(_fetch("TIMEOUT_REQUEST", 3600)),
        "DNS_BANCO": _fetch("DNS_BANCO"),
        "DOMINIO_BANCO": _fetch("DOMINIO_BANCO"),
        "RED_SEGURA_PREFIX": _fetch("RED_SEGURA_PREFIX"),
        "MOCK_PORT": int(_fetch("MOCK_PORT", 9181)),
        "JWT_SIGNING_KEY": _fetch("JWT_SIGNING_KEY"),
        "JWT_VERIFYING_KEY": _fetch("JWT_VERIFYING_KEY"),
        "SIMULADOR_SECRET_KEY": _fetch("SIMULADOR_SECRET_KEY"),
        "SIMULADOR_API_URL": _fetch("SIMULADOR_API_URL"),
        "SIMULADOR_LOGIN_URL": _fetch("SIMULADOR_LOGIN_URL"),
        "SIMULADOR_VERIFY_URL": _fetch("SIMULADOR_VERIFY_URL"),
        "SIMULADOR_USERNAME": _fetch("SIMULADOR_USERNAME"),
        "SIMULADOR_PASSWORD": _fetch("SIMULADOR_PASSWORD"),
    }

    settings["OAUTH2"] = {
        "CLIENT_ID": settings["CLIENT_ID"],
        "CLIENT_SECRET": settings["CLIENT_SECRET"],
        "ACCESS_TOKEN": settings["ACCESS_TOKEN"],
        "ORIGIN": settings["ORIGIN"],
        "OTP_URL": settings["OTP_URL"],
        "AUTH_URL": settings["AUTH_URL"],
        "API_URL": settings["API_URL"],
        "TOKEN_URL": settings["TOKEN_URL"],
        "AUTHORIZE_URL": settings["AUTHORIZE_URL"],
        "SCOPE": settings["SCOPE"],
        "REDIRECT_URI": settings["REDIRECT_URI"],
        "TIMEOUT_REQUEST": settings["TIMEOUT_REQUEST"],
        "DNS_BANCO": settings["DNS_BANCO"],
        "DOMINIO_BANCO": settings["DOMINIO_BANCO"],
        "RED_SEGURA_PREFIX": settings["RED_SEGURA_PREFIX"],
        "TIMEOUT": settings["TIMEOUT"],
        "MOCK_PORT": settings["MOCK_PORT"],
    }
    return settings