#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities to perform HTTP requests to the bank via an SSH tunnel.
This module uses sshtunnel to establish a forwarding tunnel for secure bank communication.
"""

import json
import os
from contextlib import contextmanager
from typing import Generator, Optional
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import requests
from sshtunnel import SSHTunnelForwarder

from api.gpt4.models import Transfer
from api.gpt4.utils import crear_challenge_mtan, registrar_log

# Parámetros SSH (se leen de variables de entorno)
SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

@contextmanager
def ssh_tunnel(remote_host: str, remote_port: int) -> Generator[SSHTunnelForwarder, None, None]:
    """Crea un túnel SSH que redirige remote_host:remote_port a un puerto local."""
    if not SSH_HOST or not SSH_USER:
        raise RuntimeError("Credenciales SSH no configuradas")
    server = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        ssh_pkey=SSH_KEY_PATH,
        remote_bind_address=(remote_host, remote_port),
        local_bind_address=("127.0.0.1", 0),
    )
    server.start()
    try:
        yield server
    finally:
        server.stop()


def ssh_request(
    method: str,
    remote_host: str,
    path: str,
    *,
    remote_port: int = 443,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    timeout: int = 10,
) -> requests.Response:
    """Realiza una petición HTTP mediante túnel SSH."""
    headers = headers or {}
    with ssh_tunnel(remote_host, remote_port) as tunnel:
        url = f"https://127.0.0.1:{tunnel.local_bind_port}{path}"
        response = requests.request(
            method, url, headers=headers, json=json,
            timeout=timeout, verify=False
        )
        response.raise_for_status()
        return response


@require_POST
def fake_token(request):
    """Endpoint de simulación: retorna un token falso."""
    from api.gpt4.conexion.conexion_banco import obtener_token
    token = obtener_token()
    registrar_log("BANK_SIM", tipo_log="AUTH", extra_info="Token obtenido")
    return JsonResponse({"token": token})


@require_POST
def fake_challenge_id(request):
    """Endpoint de simulación: genera un challenge OTP fake."""
    data = json.loads(request.body.decode("utf-8"))
    payment_id = data.get("payment_id")
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    challenge_id = crear_challenge_mtan(transfer, None, payment_id)  # type: ignore
    registrar_log(payment_id, tipo_log="OTP", extra_info=f"Challenge creado {challenge_id}")
    return JsonResponse({"challenge_id": challenge_id})


@require_POST
def fake_transfer(request):
    """Endpoint de simulación: procesa una transferencia fake."""
    from api.gpt4.conexion.conexion_banco import enviar_transferencia
    data = json.loads(request.body.decode("utf-8"))
    payment_id = data.get("payment_id")
    token = data.get("token")
    otp = data.get("otp")
    result = enviar_transferencia(token, payment_id, otp)
    return JsonResponse(result)


@require_GET
def fake_status(request):
    """Endpoint de simulación: consulta estado fake de transferencia."""
    from api.gpt4.conexion.conexion_banco import consultar_estado
    payment_id = request.GET.get("payment_id")
    token = request.GET.get("token")
    status = consultar_estado(token, payment_id)
    return JsonResponse(status)