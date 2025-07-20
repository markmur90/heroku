import time
import socket
import json
from functools import lru_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_GET, require_POST

import netifaces
from api.gpt4.models import Transfer
from api.gpt4.forms import SendTransferForm
from api.gpt4.utils import registrar_log
from api.gpt4.conexion.conexion_banco import (
    get_settings,
    obtener_token,
    solicitar_otp,
    enviar_transferencia,
    consultar_estado,
    make_request,

)
from api.gpt4.conexion.decorators import requiere_conexion_banco
from api.configuraciones_api.helpers import get_conf



@require_http_methods(["GET", "POST"])
def send_transfer_bank_view(request, payment_id):
    # 1) Cargamos la transferencia existente
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    # 2) Vinculamos el formulario a esa instancia para que traiga debtor_account, creditor_account, etc.
    form = SendTransferForm(request.POST or None, instance=transfer, context_mode='simple_otp')
    conf = get_settings()
    tokek_path = conf["TOKEN_PATH"]
    auth_path = conf["AUTH_PATH"]
    send_path = conf["SEND_PATH"]

    if request.method == "GET":
        try:
            # 3) Obtener token automáticamente
            token = obtener_token()
            request.session["bank_token"] = token
            # auth_url = get_conf()
            # 4) Autorizar OAuth2 simulado en el simulador
            # make_request("GET", f"/gw/oidc/authorize?payment_id={payment_id}", token=None)
            make_request("GET", f"{token_path}?payment_id={payment_id}", token=None)

            # 5) Solicitar OTP al simulador
            resp = make_request(
                # "POST", "/gw/dbapi/auth/challenges",
                "POST", auth_path,
                token=token,
                payload={"payment_id": payment_id}
            )
            otp_json = resp.json()
            challenge_id = otp_json.get("challenge_id")
            otp_generated = otp_json.get("otp")  # sólo en entorno de pruebas

            # 6) Guardar en sesión
            request.session["bank_challenge_id"] = challenge_id
            request.session["current_payment_id"] = payment_id

            # 7) Log interno y mensaje al usuario
            registrar_log(
                payment_id, tipo_log="OTP",
                extra_info=f"OTP enviado (Challenge ID: {challenge_id}, OTP: {otp_generated})"
            )
            messages.info(request, "OTP enviado. Ingresa el código para continuar.")
        except Exception as e:
            registrar_log(
                payment_id, tipo_log="ERROR",
                error=str(e), extra_info="Error al solicitar OTP"
            )
            messages.error(request, f"Error al iniciar la autenticación: {e}")
            return redirect("transfer_detailGPT4", payment_id=payment_id)

    elif request.method == "POST" and form.is_valid():
        # 8) Leemos el OTP ingresado
        otp = form.cleaned_data.get("manual_otp")
        token = request.session.get("bank_token")
        if not token:
            messages.error(request, "La sesión de autenticación expiró. Reinicia el proceso.")
            return redirect("transfer_detailGPT4", payment_id=payment_id)

        try:
            # 9) Enviar OTP para verificar y completar la transferencia
            resultado = enviar_transferencia(token, payment_id, otp)
            registrar_log(
                payment_id, tipo_log="TRANSFER",
                extra_info=f"Respuesta simulador: {resultado}"
            )

            # 10) Actualizar estado local de la transferencia
            estado = resultado.get("status")
            if not estado:
                estado = consultar_estado(token, payment_id).get("status", transfer.status)
            transfer.status = estado
            if estado == "ACCP":
                transfer.auth_id = conf["usuario"]
            transfer.save()

            messages.success(request, "Transferencia completada correctamente.")
            # 11) Limpiar la sesión tras éxito
            for k in ("bank_token", "bank_challenge_id", "current_payment_id"):
                request.session.pop(k, None)
            return redirect("transfer_detailGPT4", payment_id=payment_id)
        except Exception as e:
            registrar_log(
                payment_id, tipo_log="ERROR",
                error=str(e), extra_info="Fallo en verificación OTP/transferencia"
            )
            messages.error(request, f"Error enviando transferencia: {e}")
            return redirect("send_transfer_bank_viewGPT4", payment_id=payment_id)

    # 12) Renderizar formulario de OTP (modo simple_otp oculta campos de token)
    return render(request, "api/GPT4/send_transfer_bank.html", {
        "transfer": transfer,
        "form": form,
        "challenge_id": request.session.get("bank_challenge_id")
    })


@require_GET
@requiere_conexion_banco
def prueba_conexion_banco(request):
    """
    Prueba la conexión bancaria real o fake.
    """
    try:
        # resp = make_request("GET", "/api/transferencia")
        resp = make_request("GET", "$send_path")
        data = resp.json()
        return JsonResponse({"estado": "ok", "respuesta": data})
    except Exception as e:
        return JsonResponse({"estado": "fallo", "detalle": str(e)}, status=502)

@require_POST
@requiere_conexion_banco
def toggle_conexion_banco(request):
    """
    Alterna el uso de conexión bancaria real vs mock en sesión.
    """
    estado = request.session.get("usar_conexion_banco", False)
    request.session["usar_conexion_banco"] = not estado
    messages.success(
        request,
        f"Conexión bancaria {'activada' if not estado else 'desactivada'}."
    )
    return redirect(request.META.get("HTTP_REFERER", "/"))



from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, redirect, render
import socket

try:
    import netifaces
    usar_netifaces = True
except ImportError:
    usar_netifaces = False
    
@require_GET
def diagnostico_banco(request):
    settings = get_settings()
    dominio_banco = settings["DOMINIO_BANCO"]
    red_segura_prefix = settings["RED_SEGURA_PREFIX"]
    puerto_mock = settings["MOCK_PORT"]

    # === IP Local y Red Segura ===
    ip_local = "❌ No detectada"
    en_red_segura = False
    try:
        if usar_netifaces:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for link in addrs[netifaces.AF_INET]:
                        ip = link['addr']
                        if ip.startswith(red_segura_prefix):
                            ip_local = ip
                            en_red_segura = True
                            break
        else:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            ip_local = ip
            en_red_segura = ip.startswith(red_segura_prefix)
    except Exception as e:
        ip_local = f"❌ Error detectando IP: {e}"

    # === DNS del dominio ===
    try:
        ip_remoto = socket.gethostbyname(dominio_banco)
        dns_status = f"✅ {dominio_banco} → {ip_remoto}"
    except Exception as e:
        ip_remoto = None
        dns_status = f"❌ Error resolviendo {dominio_banco}: {e}"

    # === Acceso al puerto del mock ===
    try:
        if ip_remoto:
            with socket.create_connection((ip_remoto, puerto_mock), timeout=5):
                conexion_status = f"✅ Puerto {puerto_mock} accesible en {ip_remoto}"
        else:
            conexion_status = "⛔ No se resolvió IP, no se prueba puerto"
    except Exception as e:
        conexion_status = f"❌ Puerto {puerto_mock} no accesible: {e}"

    return render(request, "api/extras/diagnostico_banco.html", {
        "ip_local": ip_local,
        "dns_status": dns_status,
        "conexion_status": conexion_status,
        "en_red_segura": en_red_segura,
    })