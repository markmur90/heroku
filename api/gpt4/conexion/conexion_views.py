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
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = SendTransferForm(request.POST or None, context_mode='simple_otp')
    conf = get_settings()  # obtener configuraciones (usuario oficial, URLs, etc.)

    if request.method == "GET":
        try:
            # 1) Obtener token de acceso automáticamente
            token = obtener_token()
            request.session["bank_token"] = token

            # 2) Solicitar OTP al simulador (inicia desafío OTP)
            otp_response = solicitar_otp(token, payment_id)
            # Extraer ID de challenge (y OTP si se proporciona en entorno de prueba)
            challenge_id = otp_response.get("challenge_id")
            otp_generado = otp_response.get("otp")  # El OTP real enviado (solo para logging/debug)

            # Guardar en sesión para uso posterior
            request.session["bank_challenge_id"] = challenge_id
            request.session["current_payment_id"] = payment_id

            registrar_log(payment_id, tipo_log="OTP", extra_info=f"OTP enviado (Challenge ID: {challenge_id}, OTP: {otp_generado})")
            messages.info(request, "OTP enviado. Ingresa el código para continuar.")
        except Exception as e:
            # Registrar y notificar error en la fase de autenticación/OTP
            registrar_log(payment_id, tipo_log="ERROR", error=str(e), extra_info="Error al solicitar OTP")
            messages.error(request, f"Error al iniciar la autenticación: {e}")
            return redirect("transfer_detailGPT4", payment_id=payment_id)

    elif request.method == "POST" and form.is_valid():
        otp = form.cleaned_data.get("manual_otp")
        token = request.session.get("bank_token")
        if not token:
            messages.error(request, "La sesión de autenticación expiró. Reinicia el proceso.")
            return redirect("transfer_detailGPT4", payment_id=payment_id)

        try:
            # 3) Enviar OTP al simulador para completar la transferencia
            resultado = enviar_transferencia(token, payment_id, otp)
            estado_final = resultado.get("status")
            registrar_log(payment_id, tipo_log="TRANSFER", extra_info=f"Respuesta simulador: {resultado}")

            # 4) Actualizar estado (y auth_id) de la transferencia local
            if estado_final:
                transfer.status = estado_final
            else:
                # Fallback: consultar estado actual si no vino en respuesta (ej. simulador no lo retornó)
                estado_resp = consultar_estado(token, payment_id)
                transfer.status = estado_resp.get("status", transfer.status)
            if transfer.status == 'ACSC':  # éxito (Accepted Settlement Completed)
                transfer.auth_id = conf["usuario"]  # Registrar qué oficial (usuario) autorizó
            transfer.save()

            messages.success(request, "Transferencia completada correctamente.")
            # Limpieza de la sesión tras éxito
            request.session.pop("bank_token", None)
            request.session.pop("bank_challenge_id", None)
            request.session.pop("current_payment_id", None)
            return redirect("transfer_detailGPT4", payment_id=payment_id)
        except Exception as e:
            # Manejo de errores de verificación OTP o envío
            registrar_log(payment_id, tipo_log="ERROR", error=str(e), extra_info="Fallo en verificación OTP/transferencia")
            messages.error(request, f"Error enviando transferencia: {e}")
            # No limpiamos token ni datos de sesión, permitimos reintento
            return redirect("send_transfer_bank_viewGPT4", payment_id=payment_id)

    # Renderizar formulario de OTP
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
        resp = make_request("GET", "/api/transferencia")
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