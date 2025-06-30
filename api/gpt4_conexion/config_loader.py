import os
from typing import Any, Optional

class ConfigError(Exception): pass

class ConfigLoader:
    """Carga y valida configuración usando variables de entorno."""
    def __init__(self):
        self._raw = os.environ

    def get_str(self, name: str, required: bool = False) -> str:
        value = self._raw.get(name)
        if required and not value:
            raise ConfigError(f"Falta {name}")
        return value or ''

    def get_int(self, name: str, default: int = 0) -> int:
        try:
            return int(self._raw.get(name, default))
        except ValueError:
            raise ConfigError(f"{name} no es entero válido")

    def get_bool(self, name: str, default: bool = False) -> bool:
        val = self._raw.get(name)
        if val is None:
            return default
        return val.lower() in ('1','true','yes')