# config/settings/__init__.py

import os
import environ
from pathlib import Path

# Define entorno: 'local', 'heroku', 'production', etc.
DJANGO_ENV = os.getenv('DJANGO_ENV', 'production').lower()
print(f"[settings] DJANGO_ENV = {DJANGO_ENV}")

# Cargar .env.<entorno> correspondiente
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
env_path = BASE_DIR / f'.env.{DJANGO_ENV}'

if env_path.exists():
    env.read_env(env_path)
    print(f"[settings] Variables cargadas desde: {env_path}")
else:
    fallback_path = BASE_DIR / '.env'
    if fallback_path.exists():
        env.read_env(fallback_path)
        print(f"[settings] Archivo .env.{DJANGO_ENV} no encontrado. Usando fallback: {fallback_path}")
    else:
        print(f"⚠️  No se encontró .env.{DJANGO_ENV} ni .env. Continuando sin cargar variables.")

# Importa los settings según el entorno
if DJANGO_ENV == 'production':
    from .local import *
else:
    from .production import *