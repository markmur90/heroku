import hashlib
from datetime import datetime

def generate_payment_id(prefix="E2E"):
    """
    Genera un ID único basado en la fecha y hora actual con un prefijo opcional.
    Máximo 35 caracteres.
    """
    return f"{prefix}{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"[:35]


def generate_deterministic_id(*args):
    """
    Genera un ID determinista a partir de una lista de valores concatenados.
    Máximo 35 caracteres, sólo letras y números (hash SHA-256 truncado).
    """
    raw = ''.join(str(a) for a in args)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return hash_val[:35]
