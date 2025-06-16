from django.core.management.base import BaseCommand
import os
import environ
from pathlib import Path
import logging

# === BASE_DIR dinámico: raíz del proyecto ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_PATH = BASE_DIR / "logs/env_validador.log"

# === Configuración de logging ===
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='[%(asctime)s] %(message)s')

def log_to_file(msg):
    logging.info(msg)

def validar_variables():
    errores = []
    requeridas = [
        "SECRET_KEY", "DEBUG", "ALLOWED_HOSTS", "DJANGO_ENV",
        "DATABASE_URL", "DB_NAME", "DB_USER", "DB_PASS", "DB_HOST", "DB_PORT",
        "DB_CLIENT_ID", "DB_CLIENT_SECRET", "DB_API_URL", "DB_TOKEN_URL", "DB_AUTH_URL", "DB_SCOPE",
        "PRIVATE_KEY_PATH", "PRIVATE_KEY_KID", "TIMEOUT_REQUEST",
        "OAUTH2_REDIRECT_URI", "API_ORIGIN"
    ]
    for var in requeridas:
        if not os.getenv(var):
            errores.append(f"❌ FALTA VARIABLE: {var}")
    return errores

class Command(BaseCommand):
    help = 'Valida las variables del entorno y registra en env_validador.log'

    def add_arguments(self, parser):
        parser.add_argument(
            '--env',
            type=str,
            help='Entorno a validar: local, production, sandbox... (opcional)',
        )

    def handle(self, *args, **options):
        env = environ.Env()
        entorno = options['env'] or os.getenv("DJANGO_ENV", "production")
        env_file = BASE_DIR / f".env.{entorno}"

        if not env_file.exists():
            msg = f"❌ No se encontró el archivo de entorno: {env_file}"
            print(msg)
            log_to_file(msg)
            return

        # Cargar variables desde el .env
        environ.Env.read_env(str(env_file))

        linea_1 = f"[settings] DJANGO_ENV = {entorno}"
        linea_2 = f"[settings] Variables cargadas desde: {env_file}"
        errores = validar_variables()

        if errores:
            print(linea_1)
            print(linea_2)
            print("❌ Entorno inválido. Revisa el log.")
            log_to_file(linea_1)
            log_to_file(linea_2)
            for err in errores:
                log_to_file(err)
        else:
            linea_3 = "✅ Todas las variables de entorno están correctamente definidas."
            print(linea_1)
            print(linea_2)
            print(linea_3)
            log_to_file(linea_1)
            log_to_file(linea_2)
            log_to_file(linea_3)
