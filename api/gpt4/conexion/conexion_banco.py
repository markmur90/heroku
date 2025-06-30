from functools import lru_cache
from urllib.parse import urlparse
import json
import socket
import time
from typing import Any, Dict, Optional

import dns.resolver
import requests

from api.gpt4.conexion.ssh_utils import ssh_request

from api.gpt4.utils import (
    registrar_log,
    generar_xml_pain001,
    generar_archivo_aml,
    validar_xml_pain001,
    validar_aml_con_xsd,
    authorize_transfer_with_otp,
)
from api.configuraciones_api.helpers import get_conf

@lru_cache()
def get_settings() -> Dict[str, Any]:
    return {
        "BASE_URL":    get_conf("BASE_URL"),
        "TOKEN_PATH":  get_conf("TOKEN_PATH"),
        "AUTH_PATH":   get_conf("AUTH_PATH"),
        "SEND_PATH":   get_conf("SEND_PATH"),
        "STATUS_PATH": get_conf("STATUS_PATH"),
        "TIMEOUT":     int(get_conf("TIMEOUT_REQUEST")),
        "ALLOW_FAKE":  get_conf("ALLOW_FAKE_BANK") == "True",
        "USER":        get_conf("BANK_USER"),
        "PASS":        get_conf("BANK_PASS"),
    }


def esta_en_red_segura():
    conf = get_settings()
    red_prefix = conf["RED_SEGURA_PREFIX"]
    try:
        hostname = socket.gethostname()
        ip_local = socket.gethostbyname(hostname)
        return ip_local.startswith(red_prefix)
    except Exception:
        return False


def resolver_ip_dominio(dominio):
    conf = get_settings()
    dns_banco = conf["DNS_BANCO"]

    resolver = dns.resolver.Resolver()

    # Aseguramos que nameservers sea una lista de IPs
    if isinstance(dns_banco, str):
        dns_banco = [ip.strip() for ip in dns_banco.split(',') if ip.strip()]

    resolver.nameservers = dns_banco

    try:
        respuesta = resolver.resolve(dominio)
        for rdata in respuesta:
            ip = rdata.to_text()
            print(f"🔐 Resuelto {dominio} → {ip}")
            return ip
    except Exception as e:
        registrar_log("conexion", f"❌ Error DNS bancario: {e}")
        return None


def hacer_request_seguro(
    dominio,
    path="/api",
    metodo="GET",
    datos=None,
    headers=None,
    *,
    retries: int = 3,
    retry_delay: int = 1,
):
    """Realiza una petición HTTPS al banco con reintentos opcionales."""

    conf = get_settings()
    dominio_banco = conf["DOMINIO_BANCO"]
    dns_banco = conf["DNS_BANCO"]
    mock_port = conf["MOCK_PORT"]
    timeout = conf["TIMEOUT_REQUEST"]
    allow_fake_bank = conf["ALLOW_FAKE_BANK"]

    headers = headers or {}
    
    if esta_en_red_segura():
        ip_destino = resolver_ip_dominio(dominio_banco)
        if not ip_destino:
            registrar_log("conexion", f"❌ No se pudo resolver {dominio_banco} vía DNS bancario.")
            return None
    else:
        if allow_fake_bank:
            ip_destino = dns_banco
            dominio = dominio_banco
            puerto = mock_port

            if not puerto_activo(ip_destino, puerto):
                registrar_log("conexion", f"❌ Mock local en {ip_destino}:{puerto} no está activo. Cancelando.")
                return None

            registrar_log("conexion", f"⚠️ Red no segura. Usando servidor local mock en {ip_destino}:{puerto}.")
        else:
            registrar_log("conexion", "🚫 Red no segura y ALLOW_FAKE_BANK desactivado. Cancelando.")
            return None

    headers["Host"] = dominio

    for intento in range(1, retries + 1):
        try:
            r = ssh_request(
                metodo.upper(),
                dominio,
                path,
                headers=headers,
                json=datos,
                timeout=timeout,
            )
            registrar_log(
                "conexion",
                f"✅ Petición a {dominio}{path} → {r.status_code} (intento {intento})",
            )
            return r
        except Exception as e:
            registrar_log(
                "conexion",
                f"❌ Error en petición HTTPS a {dominio} (intento {intento}/{retries}): {str(e)}",
            )
            if intento == retries:
                return None
            time.sleep(retry_delay)

def puerto_activo(host, puerto, timeout=2):
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except Exception:
        return False


def make_request(
    method: str,
    path: str,
    token: str = "",
    payload: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """
    Ejecuta la petición: HTTP directo si BASE_URL incluye puerto,
    o a través de túnel SSH si no.
    """
    s = get_settings()
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = payload or {}

    parsed = urlparse(s["BASE_URL"])
    if parsed.port:
        url = s["BASE_URL"].rstrip("/") + path
        resp = requests.request(
            method,
            url,
            json=data,
            headers=headers,
            timeout=s["TIMEOUT_REQUEST"],
        )
    else:
        host = parsed.hostname or s["BASE_URL"]
        port = parsed.port or 443
        resp = ssh_request(
            method=method,
            remote_host=host,
            path=path,
            remote_port=port,
            headers=headers,
            json=data,
            timeout=s["TIMEOUT"],
        )
    resp.raise_for_status()
    return resp


def obtener_token() -> str:
    s = get_settings()
    resp = make_request(
        "POST",
        s["TOKEN_PATH"],
        payload={"username": s["BANK_USER"], "password": s["BANK_PASS"]},
    )
    return resp.json().get("access_token", "")


def solicitar_otp(token: str, payment_id: str) -> str:
    s = get_settings()
    resp = make_request(
        "POST",
        s["AUTH_PATH"],
        token=token,
        payload={"payment_id": payment_id},
    )
    return resp.json().get("challenge_id", "")


def enviar_transferencia(token: str, payment_id: str, otp: str) -> Dict[str, Any]:
    s = get_settings()
    resp = make_request(
        "POST",
        s["SEND_PATH"],
        token=token,
        payload={"payment_id": payment_id, "otp": otp},
    )
    return resp.json()


def consultar_estado(token: str, payment_id: str) -> Dict[str, Any]:
    s = get_settings()
    path = s["STATUS_PATH"] + f"/{payment_id}"
    resp = make_request(
        "GET",
        path,
        token=token,
    )
    return resp.json()
