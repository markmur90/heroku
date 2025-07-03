# File: heroku/api/gpt4/conexion/conexion_banco.py

from functools import lru_cache
from urllib.parse import urlparse
import json
import socket
import time
from typing import Any, Dict, Optional

import dns.resolver
import requests
from django.conf import settings
from api.configuraciones_api.helpers import get_conf
from api.gpt4.conexion.ssh_utils import ssh_request
from api.gpt4.models import Transfer
from api.gpt4.utils import generar_xml_pain001, registrar_log

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
        "login_url":        get_conf("SIMULADOR_LOGIN_URL"),
        "verify_url":       get_conf("SIMULADOR_VERIFY_URL"),
        "otp_url":          get_conf("OTP_URL"),
        "transfer_url":     get_conf("TRANSFER_URL"),
        "usuario":          get_conf("SIMULADOR_USERNAME"),
        "password":         get_conf("SIMULADOR_PASSWORD")
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

import requests

SIMU_BASE = "http://80.78.30.242:9181"
HEROKU_BASE = "https://api.coretransapi.com"

def login_simulador():
    response = requests.post(f"{SIMU_BASE}/auth/login", json={
        "username": "markmur88",
        "password": "Ptf8454Jd55"
    })
    return response.json()["token"]

def obtener_transferencia(payment_id: str) -> str:
    """
    Obtiene el XML PAIN.001 de la transferencia desde el modelo y lo devuelve como cadena.
    """
    try:
        transfer = Transfer.objects.get(payment_id=payment_id)
    except ObjectDoesNotExist:
        raise ValueError(f"Transferencia con payment_id '{payment_id}' no encontrada en la base de datos.")

    # Generar el XML PAIN.001 en memoria
    xml_content = generar_xml_pain001(transfer, payment_id)
    registrar_log(payment_id, tipo_log='XML', extra_info='XML PAIN.001 obtenido via modelo')
    return xml_content

def iniciar_transferencia(token, payload):
    response = requests.post(
        f"{SIMU_BASE}/api/transfers/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    return response.json()

def confirmar_transferencia(token, payment_id, otp):
    response = requests.post(
        f"{SIMU_BASE}/api/transfers/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"paymentId": payment_id, "otp": otp}
    )
    return response.json()

def ejecutar_flujo_completo():
    token = login_simulador()
    payload = {
        "paymentId": "206df230-f289-4d27-a2a5-27131ee68d72",
        "DbtrIBAN": "DE00500700100200044824",
        "CdtrIBAN": "DE00500700100200044874",
        "InstdAmt": 10.0,
        "Ccy": "EUR",
        "EndToEndId": "E2Ec1dce3c73ab85d47cf781caa4001a565",
        "InstrId": "ea376ca81f059ca30354a18022d37c13d12"
    }
    resp1 = iniciar_transferencia(token, payload)
    otp = resp1.get("otp")
    resp2 = confirmar_transferencia(token, payload["paymentId"], otp)
    return resp2



def obtener_token():
    conf = get_settings()
    response = requests.post(conf['login_url'], json={
        "username": conf["usuario"],
        "password": conf["password"]
    })
    response.raise_for_status()
    return response.json().get("access")

def solicitar_otp(token, payment_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        get_settings()['otp_url'],
        json={"payment_id": payment_id},
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def enviar_transferencia(token, payment_id, otp):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        get_settings()['verify_url'],
        json={"payment_id": payment_id, "otp": otp},
        headers=headers
    )
    response.raise_for_status()
    return response.json()
