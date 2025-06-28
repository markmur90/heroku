from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')
env_file = BASE_DIR / ('.env.production' if DJANGO_ENV == 'production' else '.env.local')
load_dotenv(env_file)

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Installed apps
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
    'api.accounts',
    'api.collection',
    'api.transactions',
    'api.transfers',
    'api.core',
    'api.authentication',
    'api.sandbox',
    'api.sct',
    'api.sepa_payment',
]

# Middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    "api.middleware.ExceptionLoggingMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.core.middleware.CurrentUserMiddleware',
]

# URL and WSGI configuration
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Templates
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
            ],
        },
    },
]

# Databases


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
        'HOST': '0.0.0.0',
        'PORT': '5432',
    }
}
DATABASES = DATABASE_PSQL

# Authentication
AUTH_USER_MODEL = 'authentication.CustomUser'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_TMP = os.path.join(BASE_DIR, 'static')

os.makedirs(STATIC_TMP, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
        #'rest_framework.permissions.AllowAny',
        
    ),
}

# OAuth2 and JWT
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'OIDC_ENABLED': True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": 'Ptf8454Jd55',
    "VERIFYING_KEY": 'Ptf8454Jd55',
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Bank API configurations
API_BASE_URL = 'https://api.db.com:443/gw/dbapi/banking/transactions/v2'
API_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
API_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

DEUTSCHE_BANK_API_URL = API_BASE_URL
DEUTSCHE_BANK_CLIENT_ID = API_CLIENT_ID
DEUTSCHE_BANK_CLIENT_SECRET = API_CLIENT_SECRET

MEMO_BANK_API_URL = API_BASE_URL
MEMO_BANK_CLIENT_ID = API_CLIENT_ID
MEMO_BANK_CLIENT_SECRET = API_CLIENT_SECRET

OAUTH_CLIENT_ID = API_CLIENT_ID
OAUTH_CLIENT_SECRET = API_CLIENT_SECRET
OAUTH_API_URL = API_BASE_URL


ACCESS_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg'

REFRESH_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc0NDc3OTcxOSwiaWF0IjoxNzQ0NjkzMzE5LCJqdGkiOiIxMGQ5ZDIzZjJhMjY0ZTMyOTkxYzVmNzQ2OTI4ZWVjNiIsInVzZXJfaWQiOjF9.Md5TQ8l8HNvba-GfIyqp3aj084DANR9X4ySCRZA6WwI'

BEARER_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'


# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "errors.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "WARNING", "propagate": True},
        "bank_services": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
    },
}

SANDBOX_API_URL = os.getenv("SANDBOX_API_URL")
API_KEY = os.getenv("API_KEY")

LOGIN_URL = '/login/'

ACCESS_TOKEN = {
    "refresh": os.getenv("REFRESH_TOKEN"),
    "access": os.getenv("ACCESS_TOKEN"),
}

# Session expiration settings
#SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
# SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Configure Django App for Heroku.
import django_heroku
django_heroku.settings(locals())