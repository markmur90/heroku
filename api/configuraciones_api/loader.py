import os
from django.core.exceptions import ImproperlyConfigured

# def cargar_variables_entorno(entorno='production'):
#     try:
#         from api.configuraciones_api.models import ConfiguracionAPI
#         configuraciones = ConfiguracionAPI.objects.filter(entorno=entorno, activo=True)
#         for config in configuraciones:
#             if config.nombre not in os.environ:
#                 os.environ[config.nombre] = config.valor
#     except Exception as e:
#         if 'no such table' in str(e).lower():
#             pass  # Primera migración: ignorar
#         else:
#             raise ImproperlyConfigured(f"Error cargando configuración desde BD: {e}")

from functools import lru_cache
from api.configuraciones_api.helpers import get_conf

@lru_cache
def get_settings():
    timeout = int(600)
    port = int(get_conf("MOCK_PORT"))
    return {
        "DNS_BANCO":            get_conf("DNS_BANCO"),
        "DOMINIO_BANCO":        get_conf("DOMINIO_BANCO"),
        "RED_SEGURA_PREFIX":    get_conf("RED_SEGURA_PREFIX"),
        "ALLOW_FAKE_BANK":      get_conf("ALLOW_FAKE_BANK"),
        "TIMEOUT":              timeout,
        "MOCK_PORT":            port,
    }
    
def cargar_variables_entorno(entorno=None, request=None):
    from api.configuraciones_api.models import ConfiguracionAPI

    if request and 'entorno_actual' in request.session:
        entorno = request.session['entorno_actual']
    elif not entorno:
        entorno = os.getenv('DJANGO_ENV', 'production')

    configuraciones = ConfiguracionAPI.objects.filter(entorno=entorno, activo=True)
    for config in configuraciones:
        if config.nombre not in os.environ:
            os.environ[config.nombre] = config.valor
