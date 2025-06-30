# config/settings/configuracion_dinamica.py
from api.configuraciones_api.helpers import get_conf

REDIRECT_URI      = get_conf('REDIRECT_URI')
CLIENT_ID         = get_conf('CLIENT_ID')
CLIENT_SECRET     = get_conf('CLIENT_SECRET')
ORIGIN            = get_conf('ORIGIN')
TOKEN_URL         = get_conf('TOKEN_URL')
OTP_URL           = get_conf('OTP_URL')
AUTH_URL          = get_conf('AUTH_URL')
API_URL           = get_conf('API_URL')
AUTHORIZE_URL     = get_conf('AUTHORIZE_URL')
SCOPE             = get_conf('SCOPE')
TIMEOUT_REQUEST   = get_conf('TIMEOUT_REQUEST')
ACCESS_TOKEN      = get_conf('ACCESS_TOKEN')
DNS_BANCO         = get_conf('DNS_BANCO')
DOMINIO_BANCO     = get_conf('DOMINIO_BANCO')
RED_SEGURA_PREFIX = get_conf('RED_SEGURA_PREFIX')
TIMEOUT           = get_conf('TIMEOUT')
MOCK_PORT         = get_conf('MOCK_PORT')

OAUTH2 = {
    'CLIENT_ID': CLIENT_ID,
    'CLIENT_SECRET': CLIENT_SECRET,
    'ACCESS_TOKEN': ACCESS_TOKEN,
    'ORIGIN': ORIGIN,
    'OTP_URL': OTP_URL,
    'AUTH_URL': AUTH_URL,
    'API_URL': API_URL,
    'TOKEN_URL': TOKEN_URL,
    'AUTHORIZE_URL': AUTHORIZE_URL,
    'SCOPE': SCOPE,
    'REDIRECT_URI': REDIRECT_URI,
    'TIMEOUT_REQUEST': TIMEOUT_REQUEST,
    'DNS_BANCO': DNS_BANCO,
    'DOMINIO_BANCO': DOMINIO_BANCO,
    'RED_SEGURA_PREFIX': RED_SEGURA_PREFIX,
    'TIMEOUT': TIMEOUT,
    'MOCK_PORT': MOCK_PORT,
}
