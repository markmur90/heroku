import os
from api.configuraciones_api.models import ConfiguracionAPI

def obtener_config(nombre, entorno='production', por_defecto=None):
    try:
        return ConfiguracionAPI.objects.get(nombre=nombre, entorno=entorno, activo=True).valor
    except ConfiguracionAPI.DoesNotExist:
        return por_defecto

def get_conf(*args, **kwargs):
    return obtener_config(*args, **kwargs)

# utils_core.py o helpers.py
def get_conf_keys(*keys):
    return (get_conf(k) for k in keys)