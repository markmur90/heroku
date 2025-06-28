import os
from django.core.exceptions import ObjectDoesNotExist

def obtener_config(nombre, entorno='production', por_defecto=None):
    try:
        from api.configuraciones_api.models import ConfiguracionAPI  # import lazy
        conf = ConfiguracionAPI.objects.get(nombre=nombre, entorno=entorno)
        return conf.valor
    except ObjectDoesNotExist:
        raise ValueError(f"No existe configuración para {nombre} en {entorno}")


def get_conf(*args, **kwargs):
    return obtener_config(*args, **kwargs)

# utils_core.py o helpers.py
def get_conf_keys(*keys):
    return (get_conf(k) for k in keys)