# api/configuraciones_api/loader.py

import os
from django.core.exceptions import ImproperlyConfigured
from functools import lru_cache

from api.configuraciones_api.helpers import get_conf

@lru_cache
def get_settings() -> dict:
    """
    Carga todas las configuraciones dinámicas desde la tabla ConfiguracionAPI
    para el entorno actual (DJANGO_ENV).
    """
    # Determinamos una sola vez el entorno
    entorno = os.getenv('DJANGO_ENV', 'production')

    # Tiempo fijo en segundos
    timeout = 600

    # Puerto (cast seguro)
    try:
        mock_port = int(get_conf("MOCK_PORT", entorno))
    except ValueError as e:
        raise ImproperlyConfigured(f"MOCK_PORT inválido para entorno {entorno}: {e}")

    return {
        "dns_banco":         get_conf("DNS_BANCO",         entorno),
        "dominio_banco":     get_conf("DOMINIO_BANCO",     entorno),
        "red_segura_prefix": get_conf("RED_SEGURA_PREFIX", entorno),
        "allow_fake_bank":   get_conf("ALLOW_FAKE_BANK",   entorno),
        "access_token":      get_conf("ACCESS_TOKEN",      entorno),
        "token_url":         get_conf("TOKEN_URL",         entorno),
        "token_path":        get_conf("TOKEN_PATH",        entorno),
        "authorize_url":     get_conf("AUTHORIZE_URL",     entorno),
        "authorize_path":    get_conf("AUTHORIZE_PATH",    entorno),
        "otp_url":           get_conf("OTP_URL",           entorno),
        "otp_path":          get_conf("OTP_PATH",          entorno),
        "auth_url":          get_conf("AUTH_URL",          entorno),
        "auth_path":         get_conf("AUTH_PATH",         entorno),
        "api_url":           get_conf("API_URL",           entorno),
        "api_path":          get_conf("API_PATH",          entorno),
        "debug":             get_conf("DEBUG",             entorno),
        "allowed_host":      get_conf("ALLOWED_HOST",      entorno),
        "secret_key":        get_conf("SECRET_KEY",        entorno),
        "environment":       get_conf("ENVIRONMENT",       entorno),
        "django_env":        entorno,  # ya lo tenemos aquí
        "redirect_uri":      get_conf("REDIRECT_URI",      entorno),
        "origin":            get_conf("ORIGIN",            entorno),
        "client_id":         get_conf("CLIENT_ID",         entorno),
        "client_secret":     get_conf("CLIENT_SECRET",     entorno),
        "scope":             get_conf("SCOPE",             entorno),
        "private_key_path":  get_conf("PRIVATE_KEY_PATH",  entorno),
        "private_key_kid":   get_conf("PRIVATE_KEY_KID",   entorno),
        "jwt_signing_key":   get_conf("JWT_SIGNING_KEY",   entorno),
        "jwt_verifying_key": get_conf("JWT_VERIFYING_KEY", entorno),
        "timeout":           timeout,
        "mock_port":         mock_port,
    }

def cargar_variables_entorno(entorno: str = None, request=None) -> None:
    """
    Vuelca todas las configuraciones activas de la tabla ConfiguracionAPI
    al entorno OS (os.environ), para que Django las lea como variables de entorno.
    Se puede forzar un 'entorno' o usar el de la sesión HTTP.
    """
    # Import lazy del modelo (asegura que apps ya estén cargadas)
    from api.configuraciones_api.models import ConfiguracionAPI

    # Si la petición tiene un entorno en sesión, lo usamos; si no, el de OS
    if request and request.session.get('entorno_actual'):
        entorno = request.session['entorno_actual']
    else:
        entorno = entorno or os.getenv('DJANGO_ENV', 'production')

    # Obtenemos sólo las configuraciones activas para ese entorno
    configuraciones = ConfiguracionAPI.objects.filter(entorno=entorno, activo=True)

    for config in configuraciones:
        # No sobreescribimos si ya está en os.environ
        os.environ.setdefault(config.nombre, config.valor)
