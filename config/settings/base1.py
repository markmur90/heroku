from datetime import timedelta
import os
from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from django.apps import apps

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 1. Creamos el lector de .env
env = environ.Env()

# 2. Detectamos el entorno (por defecto 'local') y cargamos el .env correspondiente
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local')

env_file = BASE_DIR / ('.env.production' if DJANGO_ENV == 'production' else '.env.local')
if not env_file.exists():
    raise ImproperlyConfigured(f'No se encuentra el archivo de entorno: {env_file}')
env.read_env(env_file)

# Cargar dinámicamente variables desde la BD
def intentar_cargar_variables(entorno):
    if not apps.ready:
        print("⚠️ Django apps aún no están listas. Configuración dinámica omitida.")
        return
    try:
        from api.configuraciones_api.loader import cargar_variables_entorno
        cargar_variables_entorno(entorno)
    except Exception as e:
        print(f"⚠️  Configuración dinámica no aplicada: {e}")

intentar_cargar_variables(DJANGO_ENV)

# 3. Variables críticas
SECRET_KEY = "MX2QfdeWkTc8ihotA_i1Hm7_4gYJQB4oVjOKFnuD6Cw"
DEBUG      = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '.herokuapp.com', '.coretransapi.com', '80.78.30.242', '.onion', ]



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'drf_yasg',
    'rest_framework',
    'oauth2_provider',
    'rest_framework_simplejwt',
    'corsheaders',
    'debug_toolbar',
    'rest_framework.authtoken',
    'markdownify',
    'sslserver',
    
    'api.configuraciones_api',
    'api.core',
    'api.authentication',
    'api.gpt4',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    "api.middleware.ExceptionLoggingMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'middleware.oficial_session.DetectarOficialMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.core.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'api.context_processors.entorno_actual', 
            ],
        },
    },
]

INTERNAL_IPS = ['127.0.0.1', '0.0.0.0', '193.150.']

# 5. Plantillas de base de datos
# DATABASES_HEROKU = {
#     'default': dj_database_url.config(default=env('DATABASE_URL'))
# }
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DATABASE_SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DATABASE_PSQL = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': 'markmur88',
        'PASSWORD': 'Ptf8454Jd55',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
DATABASES = DATABASE_PSQL

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_TMP = os.path.join(BASE_DIR, 'static')
os.makedirs(STATIC_TMP, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

STATICFILES_DIRS = [STATIC_TMP]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://api.db.com",
    "https://simulator-api.db.com",
    "https://apibank2-54644cdf263f.herokuapp.com",
    "https://api.coretransapi.com",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
}

OAUTH2_PROVIDER = {'ACCESS_TOKEN_EXPIRE_SECONDS': 3600, 'OIDC_ENABLED': True}

from api.configuraciones_api.loader import get_settings

SIMULATOR_URL   = "http://80.78.30.242:9181"
TOKEN_ENDPOINT  = f"{SIMULATOR_URL}/api/login/"
CHALLENGE_URL   = f"{SIMULATOR_URL}/api/challenge"
TRANSFER_URL    = f"{SIMULATOR_URL}/api/send-transfer"
STATUS_URL      = f"{SIMULATOR_URL}/api/status-transfer"

BASE_URL="http://80.78.30.242:9181"
TOKEN_PATH="/oidc/token"
AUTH_PATH="/auth/challenges"
SEND_PATH="/payments"
STATUS_PATH="/payments/status"
TIMEOUT_REQUEST=10
ALLOW_FAKE_BANK=True # Para pruebas reales, cambiar ALLOW_FAKE_BANK=False

# URLs de la API externa
TOKEN_URL="http://80.78.30.242:9181/oidc/token"
AUTHORIZE_URL="http://80.78.30.242:9181/oidc/authorize"
OTP_URL="http://80.78.30.242:9181/otp/single"
AUTH_URL="http://80.78.30.242:9181/auth/challenges"
API_URL="http://80.78.30.242:9181/payments"

REDIRECT_URI="https://api.coretransapi.com/oauth2/callback/"
ORIGIN="https://api.coretransapi.com"


SCOPE = "sepa_credit_transfers"
TIMEOUT_REQUEST = 3600

ACCESS_TOKEN = env('ACCESS_TOKEN')
CLIENT_ID = env('CLIENT_ID')
CLIENT_SECRET = env('CLIENT_SECRET')


OAUTH2 = {
    'CLIENT_ID': CLIENT_ID,
    'CLIENT_SECRET': CLIENT_SECRET,
    # 'ACCESS_TOKEN': ACCESS_TOKEN,
    'ORIGIN': ORIGIN,
    'OTP_URL': OTP_URL,
    'AUTH_URL': AUTH_URL,
    'API_URL': API_URL,
    'TOKEN_URL': TOKEN_URL,
    'AUTHORIZE_URL': AUTHORIZE_URL,
    'SCOPE': SCOPE,
    'REDIRECT_URI': REDIRECT_URI,
    'TIMEOUT': 3600,
    'TIMEOUT_REQUEST': 3600,

}

JWT_SIGNING_KEY = "Ptf8454Jd55"
JWT_VERIFYING_KEY = "Ptf8454Jd55"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "VERIFYING_KEY": JWT_VERIFYING_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{"
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{"
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "errors.log",
            "formatter": "verbose",
        },
        "app_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple"
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": True
        },
        "bank_services": {
            "handlers": ["file", "console", "app_file"],
            "level": "INFO",
            "propagate": False
        },
    },
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
# Amplía la duración de la sesión para evitar que expire durante
# el flujo de autorización OAuth2.
SESSION_COOKIE_AGE = 1800  # 30 minutos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

import django_heroku
django_heroku.settings(locals())

PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'keys', 'ecdsa_private_key.pem')
PRIVATE_KEY_KID = '6316220d-fc7b-4678-902c-1cdf60acbc8e'
