# api/gpt4/services/transfer_services.py

from sshtunnel import SSHTunnelForwarder
import requests
import time
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Credenciales SSH hacia el Simulador (superusuario Django)
SSH_HOST = "80.78.30.242"
SSH_PORT = 22
SSH_USER = "markmur88"
SSH_PASS = "Ptf8454Jd55"
REMOTE_SIM_HOST = "127.0.0.1"
REMOTE_SIM_PORT = 9181

class SSHSimulatorTunnel:
    """
    Context manager para abrir y cerrar un túnel SSH
    hacia el Simulador bancario.
    """
    def __enter__(self):
        self.tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASS,
            remote_bind_address=(REMOTE_SIM_HOST, REMOTE_SIM_PORT),
            # local_bind_address puede omitirse para puerto dinámico
        )
        self.tunnel.start()
        # Base URL apuntando al túnel local
        self.base_url = f"http://127.0.0.1:{self.tunnel.local_bind_port}"
        logger.debug(f"SSH Tunnel iniciado en {self.base_url}")
        return self.base_url

    def __exit__(self, exc_type, exc, tb):
        self.tunnel.stop()
        logger.debug("SSH Tunnel cerrado")


def obtener_token_simulador(username: str, password: str):
    """
    Llama a POST /api/generar_token pasando credenciales oficiales.
    Devuelve (token, expires_at_unix).
    """
    with SSHSimulatorTunnel() as base:
        url = f"{base}/api/generar_token/"
        resp = requests.post(url, json={"username": username, "password": password})
        resp.raise_for_status()
        data = resp.json()
        token = data["access_token"]
        expires = time.time() + data.get("expires_in", 300)
        logger.info("Token obtenido del Simulador")
        return token, expires


def generar_challenge_simulador(payment_id: str, token: str, method: str):
    """
    Llama a POST /api/challenge para generar OTP.
    `method` puede ser 'MTAN' o 'PHOTOTAN'.
    Retorna challenge_id (y opcional imagen en base64 si PhotoTAN).
    """
    with SSHSimulatorTunnel() as base:
        url = f"{base}/api/challenge/"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(url, json={"payment_id": payment_id, "method": method}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        cid = data["challenge_id"]
        img64 = data.get("image_base64")
        logger.info(f"Challenge {method} generado: {cid}")
        return cid, img64


def enviar_transferencia_simulador(payment_id: str, token: str, otp_code: str):
    """
    Llama a POST /api/transferencia con payment_id, OTP y token.
    Devuelve (True, respuesta_json) o (False, mensaje_error).
    """
    with SSHSimulatorTunnel() as base:
        url = f"{base}/api/transferencia/"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "payment_id": payment_id,
            "otp": otp_code,
        }
        resp = requests.post(url, json=payload, headers=headers)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Error en transferencia: {e} – {resp.text}")
            return False, resp.text
        data = resp.json()
        logger.info("Transferencia procesada por el Simulador")
        return True, data
