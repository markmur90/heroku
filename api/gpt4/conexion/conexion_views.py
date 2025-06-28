import json
import logging
import os
import socket
import time
import uuid
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import get_template
import dns
from weasyprint import HTML
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
import hmac
import hashlib
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone
from django.views.decorators.http import require_GET
from django.shortcuts import render
import socket
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from api.gpt4.conexion import conexion_banco
from api.gpt4.models import (
    Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent,
    PaymentIdentification, Transfer, ClientID, Kid
)
import uuid

from config import settings
from api.configuraciones_api.models import ConfiguracionAPI
from api.gpt4.models import (
    Creditor, CreditorAccount, CreditorAgent, Debtor, DebtorAccount,
    LogTransferencia, PaymentIdentification, Transfer, ClaveGenerada
)
from api.gpt4.utils import (
    BASE_SCHEMA_DIR, build_auth_url, crear_challenge_mtan,
    crear_challenge_phototan, crear_challenge_pushtan,
    fetch_token_by_code, fetch_transfer_details,
    generar_archivo_aml, generar_pdf_transferencia,
    generar_xml_pain001, generate_deterministic_id,
    generate_payment_id_uuid, generate_pkce_pair,
    get_access_token, get_client_credentials_token,
    obtener_ruta_schema_transferencia, read_log_file,
    refresh_access_token, registrar_log, registrar_log_oauth,
    resolver_challenge_pushtan, send_transfer, update_sca_request
)
from api.gpt4.conexion.conexion_banco import (
    hacer_request_banco,
    enviar_transferencia_conexion,
    obtener_token_desde_simulador,
    resolver_ip_dominio,
    get_settings as banco_settings,
)
from api.gpt4.conexion.decorators import requiere_conexion_banco
from api.gpt4.forms import (
    ClientIDForm, CreditorAccountForm, CreditorAgentForm, CreditorForm,
    DebtorAccountForm, DebtorForm, KidForm, ScaForm,
    SendTransferForm, TransferForm, ClaveGeneradaForm,
    SendTransferSimulatorForm,
)

logger = logging.getLogger(__name__)



@requiere_conexion_banco
def send_transfer_bank_view(request, payment_id):
    """Maneja el envío de transferencias usando banco real, simulador o modo fake."""
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    settings_data = banco_settings()
    allow_fake = settings_data["ALLOW_FAKE_BANK"]

    if request.GET.get("fake") == "1":
        if not allow_fake:
            return HttpResponseForbidden("Modo simulado desactivado")
        if request.method == "POST":
            transfer.status = "ACSP"
            transfer.save()
            registrar_log(payment_id, tipo_log="TRANSFER", extra_info="Transferencia simulada completada")
            return JsonResponse({"status": transfer.status})
        return render(request, "api/GPT4/send_transfer_bank.html", {"transfer": transfer, "mode": "fake"})

    if allow_fake:
        form = SendTransferSimulatorForm(request.POST or None)
        ip_sim = resolver_ip_dominio(settings_data["DOMINIO_BANCO"])
        if request.method == "GET":
            token = obtener_token_desde_simulador("493069k1", "bar1588623")
            if not token:
                messages.error(request, "No se pudo obtener token del simulador.")
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            request.session['sim_token'] = token
            try:
                challenge_id = crear_challenge_mtan(transfer, token, transfer.payment_id)
                request.session['sim_challenge'] = challenge_id
                messages.info(request, "OTP enviado por el simulador. Ingréselo para continuar.")
            except Exception as e:
                messages.error(request, str(e))
                return redirect('transfer_detailGPT4', payment_id=payment_id)
        if request.method == "POST":
            if form.is_valid():
                otp = form.cleaned_data['otp']
                token = request.session.get('sim_token')
                if not token:
                    messages.error(request, "Token de simulador no disponible.")
                    return redirect('send_transfer_bank_viewGPT4', payment_id=payment_id)
                try:
                    enviar_transferencia_conexion(request, transfer, token, otp)
                    messages.success(request, "Transferencia enviada correctamente.")
                    return redirect('transfer_detailGPT4', payment_id=payment_id)
                except Exception as e:
                    messages.error(request, str(e))
                    return redirect('transfer_detailGPT4', payment_id=payment_id)
        return render(request, "api/GPT4/send_transfer_bank.html", {"form": form, "transfer": transfer, "ip_simulator": ip_sim, "mode": "simulator"})

    form = SendTransferForm(request.POST or None, instance=transfer)
    token = None
    if request.session.get('oauth_success') and request.session.get('current_payment_id') == payment_id:
        session_token = request.session.get('access_token')
        expires = request.session.get('token_expires', 0)
        if session_token and time.time() < expires - 60:
            token = session_token
    if request.method == "POST":
        try:
            if not form.is_valid():
                registrar_log(transfer.payment_id, tipo_log='ERROR', error="Formulario inválido", extra_info="Errores en validación")
                messages.error(request, "Formulario inválido. Revisa los campos.")
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            manual_token = form.cleaned_data['manual_token']
            final_token = manual_token or token
            if not final_token:
                registrar_log(transfer.payment_id, tipo_log='AUTH', error="Token no disponible", extra_info="OAuth no iniciado o token expirado")
                request.session['return_to_send'] = True
                return redirect(f"{reverse('oauth2_authorize')}?payment_id={payment_id}")
            obtain_otp = form.cleaned_data['obtain_otp']
            manual_otp = form.cleaned_data['manual_otp']
            otp = None
            try:
                if obtain_otp:
                    method = form.cleaned_data.get('otp_method')
                    if method == 'MTAN':
                        challenge_id = crear_challenge_mtan(transfer, final_token, transfer.payment_id)
                        transfer.auth_id = challenge_id
                        transfer.save()
                        registrar_log(transfer.payment_id, tipo_log='OTP', extra_info=f"Challenge MTAN creado con ID {challenge_id}")
                        return redirect('transfer_update_scaGPT4', payment_id=transfer.payment_id)
                    elif method == 'PHOTOTAN':
                        challenge_id, img64 = crear_challenge_phototan(transfer, final_token, transfer.payment_id)
                        request.session['photo_tan_img'] = img64
                        transfer.auth_id = challenge_id
                        transfer.save()
                        registrar_log(transfer.payment_id, tipo_log='OTP', extra_info=f"Challenge PHOTOTAN creado con ID {challenge_id}")
                        return redirect('transfer_update_scaGPT4', payment_id=transfer.payment_id)
                    else:
                        otp = resolver_challenge_pushtan(crear_challenge_pushtan(transfer, final_token, transfer.payment_id), final_token, transfer.payment_id)
                elif manual_otp:
                    otp = manual_otp
                else:
                    registrar_log(transfer.payment_id, tipo_log='OTP', error="No se proporcionó OTP", extra_info="Ni automático ni manual")
                    messages.error(request, "Debes obtener o proporcionar un OTP.")
                    return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error obteniendo OTP")
                messages.error(request, str(e))
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            try:
                enviar_transferencia_conexion(request, transfer, final_token, otp)
                registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Transferencia enviada correctamente (conexion)")
                request.session.pop('access_token', None)
                request.session.pop('refresh_token', None)
                request.session.pop('token_expires', None)
                request.session.pop('oauth_success', None)
                request.session.pop('current_payment_id', None)
                messages.success(request, "Transferencia enviada correctamente.")
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error enviando transferencia (conexion)")
                messages.error(request, str(e))
                return redirect('transfer_detailGPT4', payment_id=payment_id)
        except Exception as e:
            registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error inesperado en vista")
            messages.error(request, f"Error inesperado: {str(e)}")
            return redirect('transfer_detailGPT4', payment_id=payment_id)


class ClaveGeneradaListView(ListView):
    model = ClaveGenerada
    template_name = 'api/claves/lista.html'
    context_object_name = 'claves'

class ClaveGeneradaCreateView(CreateView):
    model = ClaveGenerada
    form_class = ClaveGeneradaForm
    template_name = 'api/claves/formulario.html'
    success_url = reverse_lazy('lista_claves')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modo'] = 'crear'
        return context

class ClaveGeneradaUpdateView(UpdateView):
    model = ClaveGenerada
    form_class = ClaveGeneradaForm
    template_name = 'api/claves/formulario.html'
    success_url = reverse_lazy('lista_claves')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modo'] = 'editar'
        return context

class ClaveGeneradaDeleteView(DeleteView):
    model = ClaveGenerada
    template_name = 'api/claves/eliminar.html'
    success_url = reverse_lazy('lista_claves')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clave'] = self.get_context_data
        return context



# ============================
# Toggle y prueba conexión banco
# ============================


@require_GET
@requiere_conexion_banco
def prueba_conexion_banco(request):
    respuesta = hacer_request_banco(request, path="/api/transferencia")
    if respuesta is None:
        return JsonResponse({"estado": "fallo", "detalle": "No se obtuvo respuesta."}, status=502)
    return JsonResponse({"estado": "ok", "respuesta": respuesta})

def toggle_conexion_banco(request):
    estado_actual = request.session.get("usar_conexion_banco", False)
    request.session["usar_conexion_banco"] = not estado_actual
    estado = "activada" if not estado_actual else "desactivada"
    messages.success(request, f"Conexión bancaria {estado}.")
    return redirect(request.META.get("HTTP_REFERER", "/"))

# @require_GET
# def prueba_conexion_banco(request):
#     respuesta = hacer_request_banco(request, path="/api/test")
#     if respuesta is None:
#         return JsonResponse({"estado": "fallo", "detalle": "No se obtuvo respuesta."}, status=502)
#     return JsonResponse({"estado": "ok", "respuesta": respuesta})


# ============================
# Diagnóstico de red bancaria
# ============================
# ==== Configuración general ====
from functools import lru_cache
from api.configuraciones_api.helpers import get_conf
import netifaces

@lru_cache
def get_settings():
    return {
        "DNS_BANCO":            get_conf("DNS_BANCO"),
        "DOMINIO_BANCO":        get_conf("DOMINIO_BANCO"),
        "RED_SEGURA_PREFIX":    get_conf("RED_SEGURA_PREFIX"),
        "TIMEOUT":              int(get_conf("TIMEOUT")),
        "MOCK_PORT":            int(get_conf("MOCK_PORT")),
    }


# Ejemplo de uso:
# settings = get_settings()
# token_url = settings["TOKEN_URL"]


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








# ============================
# Simulación de red bancaria
# ============================
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from datetime import timedelta
from api.gpt4.conexion import conexion_banco
from api.gpt4.models import (
    Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent,
    PaymentIdentification, Transfer, ClientID, Kid
)
import uuid

@method_decorator(staff_member_required, name='dispatch')
class SimulacionTransferenciaView(View):
    def get(self, request):
        # Forzamos red segura
        conexion_banco.esta_en_red_segura = lambda: True

        # Usuario con permisos: usar username existente de oficial
        User = get_user_model()
        oficial = User.objects.get(username='493069k1')  # cambia este username

        # Crear entidades necesarias
        debtor = Debtor.objects.create(
            name="Cliente Simulado",
            customer_id="SIMU1234567890",
            postal_address_country="ES",
            postal_address_street="Calle Falsa 123",
            postal_address_city="Madrid"
        )
        debtor_account = DebtorAccount.objects.create(
            debtor=debtor,
            iban="ES7620770024003102575766"
        )
        creditor = Creditor.objects.create(
            name="Beneficiario Externo",
            postal_address_country="DE",
            postal_address_street="Berlinerstrasse 99",
            postal_address_city="Berlin"
        )
        creditor_account = CreditorAccount.objects.create(
            creditor=creditor,
            iban="DE89370400440532013000"
        )
        creditor_agent = CreditorAgent.objects.create(
            bic="MARKDEF1100",
            financial_institution_id="BANKDEFFXXX",
            other_information="Banco Externo XYZ"
        )
        payment_ident = PaymentIdentification.objects.create(
            instruction_id=str(uuid.uuid4()),
            end_to_end_id=str(uuid.uuid4())
        )
        clientid = ClientID.objects.first()
        kid = Kid.objects.first()

        transfer = Transfer.objects.create(
            payment_id=str(uuid.uuid4()),
            client=clientid,
            kid=kid,
            debtor=debtor,
            debtor_account=debtor_account,
            creditor=creditor,
            creditor_account=creditor_account,
            creditor_agent=creditor_agent,
            instructed_amount=1000.00,
            currency="EUR",
            purpose_code="GDSV",
            requested_execution_date=timezone.now().date() + timedelta(days=1),
            remittance_information_unstructured="Simulación de transferencia SEPA",
            status="CREA",
            payment_identification=payment_ident,
            auth_id="simu-auth"
        )

        return HttpResponse(f"✅ Transferencia simulada creada con ID: {transfer.payment_id}")


@require_POST
def bank_sim_token(request):
    """Obtiene un token desde el simulador bancario"""
    username = get_conf("BANK_SIM_USER", "493069k1")
    password = get_conf("BANK_SIM_PASS", "bar1588623")
    token = obtener_token_desde_simulador(username, password)
    if token:
        registrar_log("BANK_SIM", tipo_log="AUTH", extra_info="Token obtenido")
        return JsonResponse({"token": token})
    return JsonResponse({"error": "No se pudo obtener token"}, status=500)


@require_POST
def bank_sim_challenge(request):
    data = json.loads(request.body.decode("utf-8"))
    payment_id = data.get("payment_id")
    token = data.get("token")
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    challenge_id = crear_challenge_mtan(transfer, token, payment_id)
    registrar_log(payment_id, tipo_log="OTP", extra_info=f"Challenge creado {challenge_id}")
    return JsonResponse({"challenge_id": challenge_id})


@require_POST
def bank_sim_send_transfer(request):
    data = json.loads(request.body.decode("utf-8"))
    payment_id = data.get("payment_id")
    token = data.get("token")
    otp = data.get("otp")
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    resp = enviar_transferencia_conexion(request, transfer, token, otp)
    if isinstance(resp, requests.Response):
        result = resp.json()
    else:
        result = resp
    return JsonResponse(result)


@require_GET
def bank_sim_status_transfer(request):
    payment_id = request.GET.get("payment_id")
    token = request.GET.get("token")
    path = f"/api/transferencia/{payment_id}" if payment_id else "/api/transferencia"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = hacer_request_banco(request, path=path, headers=headers)
    if isinstance(resp, requests.Response):
        data = resp.json()
    else:
        data = resp
    return JsonResponse(data)

