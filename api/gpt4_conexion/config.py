# config.py
import os
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Carga automática según entorno
env_file = f".env.{os.getenv('DJANGO_ENV', 'development')}"
load_dotenv(env_file)

class Settings(BaseSettings):
    DJANGO_ENV: str = Field(..., description="Entorno de ejecución: development|staging|production")
    SECRET_KEY: str
    BANK_HOST: str
    BANK_PORT: int
    BANK_VERIFY_SSL: bool = True
    BANK_TIMEOUT: int = 10
    BANK_RETRIES: int = 3
    RED_SEGURA_PREFIX: str = Field(..., description="Prefijo de red segura (CIDR)")

    class Config:
        env_file = env_file
        env_file_encoding = 'utf-8'

settings = Settings()