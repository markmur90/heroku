# config/settings/configuracion_dinamica.py
from .env_vars import load_env

env_settings = load_env()

REDIRECT_URI      = env_settings['REDIRECT_URI']
CLIENT_ID         = env_settings['CLIENT_ID']
CLIENT_SECRET     = env_settings['CLIENT_SECRET']
ORIGIN            = env_settings['ORIGIN']
TOKEN_URL         = env_settings['TOKEN_URL']
OTP_URL           = env_settings['OTP_URL']
AUTH_URL          = env_settings['AUTH_URL']
API_URL           = env_settings['API_URL']
AUTHORIZE_URL     = env_settings['AUTHORIZE_URL']
SCOPE             = env_settings['SCOPE']
TIMEOUT_REQUEST   = env_settings['TIMEOUT_REQUEST']
ACCESS_TOKEN      = env_settings['ACCESS_TOKEN']
DNS_BANCO         = env_settings['DNS_BANCO']
DOMINIO_BANCO     = env_settings['DOMINIO_BANCO']
RED_SEGURA_PREFIX = env_settings['RED_SEGURA_PREFIX']
TIMEOUT           = env_settings['TIMEOUT']
MOCK_PORT         = env_settings['MOCK_PORT']

OAUTH2 = env_settings['OAUTH2']


def get_oauth2_settings() -> dict:
    """Return a copy of the dynamic OAUTH2 configuration."""
    return OAUTH2.copy()