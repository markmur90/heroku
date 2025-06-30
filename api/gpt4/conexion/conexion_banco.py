# File: heroku/api/gpt4/conexion/conexion_banco.py

from functools import lru_cache
from urllib.parse import urlparse
import json
import socket
import time
from typing import Any, Dict, Optional

import dns.resolver
import requests

from api.configuraciones_api.helpers import get_conf
from api.gpt4.conexion.ssh_utils import ssh_request
from api.gpt4.utils import registrar_log

@lru_cache()
def get_settings() -> Dict[str, Any]:
    """Return all configuration values needed for the bank connection."""
    return {
        "BASE_URL":         get_conf("BASE_URL"),
        "TOKEN_PATH":       get_conf("TOKEN_PATH"),
        "AUTH_PATH":        get_conf("AUTH_PATH"),
        "SEND_PATH":        get_conf("SEND_PATH"),
        "STATUS_PATH":      get_conf("STATUS_PATH"),
        "TIMEOUT_REQUEST":  int(get_conf("TIMEOUT_REQUEST")),
        "DNS_BANCO":        get_conf("DNS_BANCO"),
        "DOMINIO_BANCO":    get_conf("DOMINIO_BANCO"),
        "RED_SEGURA_PREFIX": get_conf("RED_SEGURA_PREFIX"),
        "MOCK_PORT":        int(get_conf("MOCK_PORT")),
        "ALLOW_FAKE_BANK":  get_conf("ALLOW_FAKE_BANK") == "True",
        "BANK_USER":        get_conf("BANK_USER"),
        "BANK_PASS":        get_conf("BANK_PASS"),
    }


def esta_en_red_segura() -> bool:
    """Determina si estamos en la red segura del banco."""
    conf = get_settings()
    red_prefix = conf["RED_SEGURA_PREFIX"]
    try:
        ip_local = socket.gethostbyname(socket.gethostname())
        return ip_local.startswith(red_prefix)
    except Exception as e:
        registrar_log("conexion", f"❌ Error determinando red segura: {e}")
        return False


def resolver_ip_dominio(dominio: str) -> Optional[str]:
    """Resuelve el dominio bancario a su IP mediante DNS específico."""
    conf = get_settings()
    dns_banco = conf["DNS_BANCO"]
    resolver = dns.resolver.Resolver()
    if isinstance(dns_banco, str):
        dns_banco = [ip.strip() for ip in dns_banco.split(',') if ip.strip()]
    resolver.nameservers = dns_banco

    try:
        respuesta = resolver.resolve(dominio)
        for rdata in respuesta:
            ip = rdata.to_text()
            registrar_log("conexion", f"🔐 Resuelto {dominio} → {ip}")
            return ip
    except Exception as e:
        registrar_log("conexion", f"❌ Error DNS bancario: {e}")
    return None


def puerto_activo(host: str, puerto: int, timeout: int = 2) -> bool:
    """Verifica si el puerto está escuchando en el host dado."""
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except Exception as e:
        registrar_log("conexion", f"❌ Puerto inaccesible {host}:{puerto} - {e}")
        return False


def make_request(
    method: str,
    path: str,
    token: str = "",
    payload: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """
    Ejecuta petición HTTP/HTTPS al simulador bancario.
    Usa túnel SSH si no hay puerto explícito en BASE_URL, o un mock local si se permite.
    """
    s = get_settings()
    data = payload or {}
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    parsed = urlparse(s["BASE_URL"])
    # Si BASE_URL incluye puerto, hacer request directo
    if parsed.port:
        url = s["BASE_URL"].rstrip("/") + path
        registrar_log("conexion", f"➡️ {method} {url}")
        resp = requests.request(
            method,
            url,
            json=data,
            headers=headers,
            timeout=s["TIMEOUT_REQUEST"],
        )
    else:
        # Conexión via SSH o mock
        host_domain = parsed.hostname or s["DOMINIO_BANCO"]
        port = parsed.port or 443

        if esta_en_red_segura():
            ip_destino = resolver_ip_dominio(host_domain)
            if ip_destino:
                remote_host = ip_destino
                remote_port = port
            else:
                raise RuntimeError(f"No se pudo resolver DNS de {host_domain}")
        else:
            if s["ALLOW_FAKE_BANK"]:
                remote_host = host_domain
                remote_port = s["MOCK_PORT"]
                if not puerto_activo(remote_host, remote_port):
                    raise RuntimeError(f"Mock no disponible en {remote_host}:{remote_port}")
                registrar_log("conexion", f"⚠️ Usando mock en {remote_host}:{remote_port}")
            else:
                raise RuntimeError("Red no segura y mock desactivado")

        headers["Host"] = host_domain
        registrar_log("conexion", f"🔐 SSH tunnel -> {remote_host}:{remote_port}{path}")
        resp = ssh_request(
            method.upper(),
            remote_host,
            path,
            remote_port=remote_port,
            headers=headers,
            json=data,
            timeout=s["TIMEOUT_REQUEST"],
        )

    try:
        resp.raise_for_status()
    except Exception as e:
        registrar_log("conexion", f"❌ HTTP Error {method} {path}: {e}")
        raise

    registrar_log("conexion", f"✅ {method} {path} → {resp.status_code}")
    return resp


def obtener_token() -> str:
    """Solicita token JWT al simulador bancario."""
    s = get_settings()
    resp = make_request(
        "POST",
        s["TOKEN_PATH"],
        payload={"username": s["BANK_USER"], "password": s["BANK_PASS"]},
    )
    return resp.json().get("token") or resp.json().get("access_token", "")


def solicitar_otp(token: str, payment_id: str) -> str:
    """Solicita OTP para la transferencia identficada."""
    s = get_settings()
    resp = make_request(
        "POST",
        s["AUTH_PATH"],
        token=token,
        payload={"payment_id": payment_id},
    )
    return resp.json().get("challenge_id", "")


def enviar_transferencia(token: str, payment_id: str, otp: str) -> Dict[str, Any]:
    """Envía la transferencia al simulador bancario."""
    s = get_settings()
    resp = make_request(
        "POST",
        s["SEND_PATH"],
        token=token,
        payload={"payment_id": payment_id, "otp": otp},
    )
    return resp.json()


def consultar_estado(token: str, payment_id: str) -> Dict[str, Any]:
    """Consulta el estado de una transferencia."""
    s = get_settings()
    path = s["STATUS_PATH"] + f"/{payment_id}"
    resp = make_request(
        "GET",
        path,
        token=token,
    )
    return resp.json()
