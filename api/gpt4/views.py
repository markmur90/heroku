# /home/markmur88/api_bank_h2/api/gpt4/views.py
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
    resolver_challenge_pushtan, send_transfer, update_sca_request,
    wait_for_final_status
)
from api.gpt4_conexion.conexion_banco_refactor import (
    hacer_request_banco,
    enviar_transferencia_conexion,
    obtener_token_desde_simulador,
)
from api.gpt4.conexion.conexion_banco import (
    resolver_ip_dominio,
    get_settings as banco_settings,
)
from api.gpt4.conexion.decorators import requiere_conexion_banco
from api.gpt4.forms import (
    ClientIDForm, CreditorAccountForm, CreditorAgentForm, CreditorForm,
    DebtorAccountForm, DebtorForm, KidForm, ScaForm,
    SendTransferForm, TransferForm, ClaveGeneradaForm,
)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def handle_notification(request):
    try:
        # 1️⃣ Obtener el secret para el webhook
        secret = ConfiguracionAPI.objects.get(
            nombre='WEBHOOK_SECRET',
            entorno='production'
        ).valor

        # 2️⃣ Validar firma HMAC SHA-256 en cabecera X-Signature
        signature = request.headers.get('X-Signature', '')
        expected_sig = hmac.new(
            key=force_bytes(secret),
            msg=request.body,
            digestmod=hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return HttpResponseForbidden('Invalid signature')

        # 3️⃣ Registrar petición entrante en logs
        payload = request.body.decode('utf-8')
        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
        registro = (
            request.GET.get('registro')
            or request.headers.get('X-Request-Id')
            or f"AUTOLOG-{now().timestamp()}"
        )
        registrar_log(
            registro=registro,
            tipo_log='NOTIFICACION',
            headers_enviados=headers,
            request_body=payload,
            extra_info="Notificación automática recibida en webhook"
        )
        LogTransferencia.objects.create(
            registro=registro,
            tipo_log='NOTIFICACION',
            contenido=payload
        )

        # 4️⃣ Procesar payload y actualizar estado de la transferencia
        data = json.loads(payload)
        payment_id = data.get('paymentId')
        status     = data.get('transactionStatus')
        if payment_id and status:
            Transfer.objects.filter(payment_id=payment_id).update(status=status)
            registrar_log(
                registro=payment_id,
                tipo_log='NOTIFICACION',
                extra_info=f"Transferencia {payment_id} actualizada a estado {status}"
            )

        # 5️⃣ Responder 204 No Content
        return HttpResponse(status=204)

    except ConfiguracionAPI.DoesNotExist:
        registrar_log(
            registro='NOTIF_CONFIG_ERROR',
            tipo_log='ERROR',
            error='WEBHOOK_SECRET no configurado',
            extra_info="Falta configuración de WEBHOOK_SECRET"
        )
        return JsonResponse(
            {'status': 'error', 'mensaje': 'Webhook secret no configurado'},
            status=500
        )

    except Exception as e:
        registrar_log(
            registro='NOTIF_ERROR',
            tipo_log='ERROR',
            error=str(e),
            extra_info="Error procesando notificación entrante"
        )
        return JsonResponse(
            {'status': 'error', 'mensaje': str(e)},
            status=500
        )


# ==== DEBTOR ====
def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_debtorsGPT4')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT4/create_debtor.html', {'form': form})

def list_debtors(request):
    debtors = Debtor.objects.all()
    return render(request, 'api/GPT4/list_debtor.html', {'debtors': debtors})


# ==== DEBTOR ACCOUNT ====
def create_debtor_account(request):
    if request.method == 'POST':
        form = DebtorAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_debtor_accountsGPT4')
    else:
        form = DebtorAccountForm()
    return render(request, 'api/GPT4/create_debtor_account.html', {'form': form})

def list_debtor_accounts(request):
    accounts = DebtorAccount.objects.all()
    return render(request, 'api/GPT4/list_debtor_accounts.html', {'accounts': accounts})


# ==== CREDITOR ====
def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditorsGPT4')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT4/create_creditor.html', {'form': form})

def list_creditors(request):
    creditors = Creditor.objects.all()
    return render(request, 'api/GPT4/list_creditors.html', {'creditors': creditors})


# ==== CREDITOR ACCOUNT ====
def create_creditor_account(request):
    if request.method == 'POST':
        form = CreditorAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditor_accountsGPT4')
    else:
        form = CreditorAccountForm()
    return render(request, 'api/GPT4/create_creditor_account.html', {'form': form})

def list_creditor_accounts(request):
    accounts = CreditorAccount.objects.all()
    return render(request, 'api/GPT4/list_creditor_accounts.html', {'accounts': accounts})


# ==== CREDITOR AGENT ====
def create_creditor_agent(request):
    if request.method == 'POST':
        form = CreditorAgentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditor_agentsGPT4')
    else:
        form = CreditorAgentForm()
    return render(request, 'api/GPT4/create_creditor_agent.html', {'form': form})

def list_creditor_agents(request):
    agents = CreditorAgent.objects.all()
    return render(request, 'api/GPT4/list_creditor_agents.html', {'agents': agents})


# ==== CLIENT ID ====
def create_clientid(request):
    if request.method == 'POST':
        form = ClientIDForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_transferGPT4')
    else:
        form = ClientIDForm()
    return render(request, 'api/GPT4/create_clientid.html', {'form': form})

# ==== KID ====
def create_kid(request):
    if request.method == 'POST':
        form = KidForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_transferGPT4')
    else:
        form = KidForm()
    return render(request, 'api/GPT4/create_kid.html', {'form': form})


# ==== TRANSFER ====
def create_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.payment_id = str(generate_payment_id_uuid())
            payment_identification = PaymentIdentification.objects.create(
                instruction_id=generate_deterministic_id(
                    transfer.payment_id,
                    transfer.creditor_account.iban,
                    transfer.instructed_amount
                ),
                end_to_end_id=generate_deterministic_id(
                    transfer.debtor_account.iban,
                    transfer.creditor_account.iban,
                    transfer.instructed_amount,
                    transfer.requested_execution_date,
                    prefix="E2E"
                )
            )
            transfer.payment_identification = payment_identification
            transfer.save()

            registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Transferencia creada")
            generar_xml_pain001(transfer, transfer.payment_id)
            # registrar_log(transfer.payment_id, tipo_log='XML', extra_info="Archivo pain.001 generado")

            generar_archivo_aml(transfer, transfer.payment_id)
            # registrar_log(transfer.payment_id, tipo_log='AML', extra_info="Archivo AML generado")

            messages.success(request, "Transferencia creada y XML/AML generados correctamente.")
            return redirect('dashboard')
        else:
            registrar_log("SIN_ID", tipo_log='ERROR', error="Formulario inválido en creación", extra_info="Errores en campos del TransferForm")
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = TransferForm()
    return render(request, 'api/GPT4/create_transfer.html', {'form': form, 'transfer': None})


def list_transfers(request):
    estado = request.GET.get("estado")
    transfers = Transfer.objects.all().order_by('-created_at')

    if estado in ["PNDG", "RJCT", "ACSP"]:
        transfers = transfers.filter(status=estado)
        registrar_log("LISTA", tipo_log='TRANSFER', extra_info=f"Listado filtrado por estado: {estado}")
    else:
        registrar_log("LISTA", tipo_log='TRANSFER', extra_info="Listado completo de transferencias")

    paginator = Paginator(transfers, 10)
    page_number = request.GET.get('page', 1)
    try:
        transfers_paginated = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        registrar_log("LISTA", tipo_log='ERROR', error="Página inválida solicitada", extra_info=f"page={page_number}")
        transfers_paginated = paginator.page(1)

    return render(request, 'api/GPT4/list_transfer.html', {
        'transfers': transfers_paginated
    })


def transfer_detail(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    # registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Vista de detalle accedida")

    log_content = read_log_file(transfer.payment_id)
    logs_db = LogTransferencia.objects.filter(registro=transfer.payment_id).order_by('-created_at')

    logs_por_tipo = {
        'transferencia': logs_db.filter(tipo_log='TRANSFER'),
        'autenticacion': logs_db.filter(tipo_log='AUTH'),
        'errores': logs_db.filter(tipo_log='ERROR'),
        'xml': logs_db.filter(tipo_log='XML'),
        'aml': logs_db.filter(tipo_log='AML'),
        'sca': logs_db.filter(tipo_log='SCA'),
        'otp': logs_db.filter(tipo_log='OTP'),
    }

    errores_detectados = logs_db.filter(tipo_log='ERROR')
    mensaje_error = errores_detectados.first().contenido if errores_detectados.exists() else None # type: ignore

    carpeta = obtener_ruta_schema_transferencia(transfer.payment_id)
    archivos_logs = {
        archivo: os.path.join(carpeta, archivo)
        for archivo in os.listdir(carpeta)
        if archivo.endswith(".log")
    }

    log_files_content = {}
    errores_detectados = []
    for nombre, ruta in archivos_logs.items():
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                log_files_content[nombre] = contenido
                if "=== Error ===" in contenido:
                    mensaje_error = contenido.split("=== Error ===")[-1].strip().split("===")[0].strip()
        else:
            registrar_log(transfer.payment_id, tipo_log='ERROR', error=f"Archivo log no encontrado: {nombre}")

    archivos = {
        'pain001': os.path.join(carpeta, f"pain001_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain001_{transfer.payment_id}.xml")) else None,
        'aml': os.path.join(carpeta, f"aml_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"aml_{transfer.payment_id}.xml")) else None,
        'pain002': os.path.join(carpeta, f"pain002_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain002_{transfer.payment_id}.xml")) else None,
    }

    for contenido in log_files_content.values():
        if "Error" in contenido or "Traceback" in contenido or "no válido según el XSD" in contenido:
            errores_detectados.append(contenido)

    return render(request, 'api/GPT4/transfer_detail.html', {
        'transfer': transfer,
        'log_files_content': log_files_content,
        'logs_por_tipo': logs_por_tipo,
        'log_content': log_content,
        'archivos': archivos,
        'errores_detectados': errores_detectados,
        'mensaje_error': mensaje_error,
        'allow_fake_bank': banco_settings()["ALLOW_FAKE_BANK"],
    })


def transfer_update_sca(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = ScaForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            action = form.cleaned_data['action']
            otp = form.cleaned_data['otp']
            try:
                token = get_access_token(transfer.payment_id)
                update_sca_request(transfer, action, otp, token)
                if transfer.status == 'PDNG':
                    wait_for_final_status(transfer, token)
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error procesando SCA en vista")
                mensaje_error = str(e)
                return _render_transfer_detail(request, transfer, mensaje_error)
        else:
            registrar_log(transfer.payment_id, tipo_log='ERROR', error="Formulario SCA inválido", extra_info="Errores validación SCA")
            mensaje_error = "Por favor corrige los errores en la autorización."
            return _render_transfer_detail(request, transfer, mensaje_error)
    return render(request, 'api/GPT4/transfer_sca.html', {'form': form, 'transfer': transfer})


def _render_transfer_detail(request, transfer, mensaje_error=None, details=None):
    if mensaje_error:
        registrar_log(
            transfer.payment_id,
            tipo_log='TRANSFER',
            error=mensaje_error,
            extra_info="Renderizando vista de detalle tras error"
        )
    else:
        registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Renderizando vista de detalle sin errores")

    log_content = read_log_file(transfer.payment_id)
    carpeta = obtener_ruta_schema_transferencia(transfer.payment_id)
    archivos = {
        nombre_base: os.path.join(carpeta, f"{nombre_base}_{transfer.payment_id}.xml")
        if os.path.exists(os.path.join(carpeta, f"{nombre_base}_{transfer.payment_id}.xml"))
        else None
        for nombre_base in ("pain001", "aml", "pain002")
    }

    log_files_content = {}
    errores_detectados = []
    try:
        for fichero in os.listdir(carpeta):
            if fichero.lower().endswith(".log"):
                ruta = os.path.join(carpeta, fichero)
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                except (IOError, OSError) as e:
                    contenido = f"Error al leer el log {fichero}: {e}"
                    errores_detectados.append(contenido)
                log_files_content[fichero] = contenido
                if any(p in contenido for p in ("Error", "Traceback", "no válido según el XSD")):
                    errores_detectados.append(contenido)
    except (IOError, OSError):
        mensaje_error = mensaje_error or "No se pudo acceder a los logs de la transferencia."

    contexto = {
        'transfer': transfer,
        'log_content': log_content,
        'archivos': archivos,
        'log_files_content': log_files_content,
        'errores_detectados': errores_detectados,
        'mensaje_error': mensaje_error,
        'details': details,
        'allow_fake_bank': banco_settings()["ALLOW_FAKE_BANK"],
    }
    return render(request, "api/GPT4/transfer_detail.html", contexto)


def edit_transfer(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    if request.method == "POST":
        form = TransferForm(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            # registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Transferencia editada correctamente")
            messages.success(request, "Transferencia actualizada correctamente.")
            return redirect('transfer_detailGPT4', payment_id=payment_id)
        else:
            # registrar_log(transfer.payment_id, tipo_log='ERROR', error="Formulario de edición inválido", extra_info="Errores en campos")
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = TransferForm(instance=transfer)
        # registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Accediendo a vista de edición de transferencia")
    return render(request, 'api/GPT4/edit_transfer.html', {
        'form': form,
        'transfer': transfer
    })



# ==== PDF ====
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(Transfer, payment_id=payment_id)
    generar_pdf_transferencia(transferencia)
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    pdf_file = next(
        (os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".pdf") and payment_id in f),
        None
    )
    if not pdf_file or not os.path.exists(pdf_file):
        messages.error(request, "El archivo PDF no se encuentra disponible.")
        return redirect('transfer_detailGPT4', payment_id=transferencia.payment_id)
    return FileResponse(open(pdf_file, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_file))

# ==== OAUTH2 ====

def oauth2_authorize(request):
    if not settings.USE_OAUTH2_UI:
        registrar_log_oauth("flujo_bloqueado", "entorno_sin_ui", request=request)
        messages.warning(request, "Autorización OAuth deshabilitada en este entorno.")
        return redirect("dashboard")

    try:
        payment_id = request.GET.get('payment_id')
        if not payment_id:
            registrar_log_oauth("inicio_autorizacion", "error", {"error": "Falta payment_id"}, "OAuth2 requiere un payment_id", request=request)
            registrar_log(payment_id, tipo_log="ERROR", error="OAuth2 requiere un payment_id", extra_info="Falta payment_id en GET")
            messages.error(request, "Debes iniciar autorización desde una transferencia específica.")
            return redirect('dashboard')

        transfer = Transfer.objects.get(payment_id=payment_id)
        verifier, challenge = generate_pkce_pair()
        state = uuid.uuid4().hex
        request.session.update({
            'pkce_verifier': verifier,
            'oauth_state': state,
            'oauth_in_progress': True,
            'oauth_start_time': time.time(),
            'current_payment_id': transfer.payment_id
        })

        auth_url = build_auth_url(state, challenge)
        registrar_log_oauth("inicio_autorizacion", "exito", {
            "state": state,
            "auth_url": auth_url,
            "code_challenge": challenge,
            "payment_id": transfer.payment_id
        }, request=request)
        registrar_log(transfer.payment_id, tipo_log="AUTH", request_body={
            "verifier": verifier,
            "challenge": challenge,
            "state": state
        }, extra_info="Inicio del flujo OAuth2 desde transferencia")

        return render(request, 'api/GPT4/oauth2_authorize.html', {
            'auth_url': auth_url,
            'payment_id': transfer.payment_id
        })

    except Exception as e:
        registrar_log_oauth("inicio_autorizacion", "error", None, str(e), request=request)
        registrar_log(str(Transfer.payment_id), tipo_log="ERROR", error=str(e), extra_info="Excepción en oauth2_authorize")
        messages.error(request, f"Error iniciando autorización OAuth2: {str(e)}")
        return render(request, 'api/GPT4/oauth2_callback.html', {'auth_url': None})


def oauth2_callback(request):
    if not settings.USE_OAUTH2_UI:
        registrar_log_oauth("callback", "bloqueado", {"razon": "entorno_sin_ui"}, request=request)
        messages.warning(request, "Callback OAuth deshabilitado en este entorno.")
        return redirect("dashboard")

    try:
        if not request.session.get('oauth_in_progress', False):
            registrar_log_oauth("callback", "fallo", {"razon": "flujo_no_iniciado"}, request=request)
            registrar_log(str(Transfer.payment_id), tipo_log="ERROR", error="Flujo OAuth no iniciado", extra_info="callback sin sesión válida")
            messages.error(request, "No hay una autorización en progreso")
            return redirect('dashboard')

        request.session['oauth_in_progress'] = False

        if 'error' in request.GET:
            registrar_log_oauth("callback", "fallo", {
                "error": request.GET.get('error'),
                "error_description": request.GET.get('error_description', ''),
                "params": dict(request.GET)
            }, request=request)
            registrar_log(str(Transfer.payment_id), tipo_log="ERROR", error="OAuth error", extra_info=f"{request.GET}")
            messages.error(request, f"Error en autorización: {request.GET.get('error')}")
            return render(request, 'api/GPT4/oauth2_callback.html')

        state = request.GET.get('state')
        session_state = request.session.get('oauth_state')
        if state != session_state:
            registrar_log_oauth("callback", "fallo", {
                "razon": "state_mismatch",
                "state_recibido": state,
                "state_esperado": session_state
            }, request=request)
            registrar_log(str(Transfer.payment_id), tipo_log="ERROR", error="State mismatch en OAuth callback", extra_info=f"Recibido: {state} / Esperado: {session_state}")
            messages.error(request, "Error de seguridad: State mismatch")
            return render(request, 'api/GPT4/oauth2_callback.html')

        code = request.GET.get('code')
        verifier = request.session.pop('pkce_verifier', None)
        registrar_log_oauth("callback", "procesando", {
            "code": code,
            "state": state
        }, request=request)

        access_token, refresh_token, expires = fetch_token_by_code(code, verifier)

        request.session.update({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expires': time.time() + expires,
            'oauth_success': True
        })

        registrar_log_oauth("obtencion_token", "exito", {
            "token_type": "Bearer",
            "expires_in": expires,
            "scope": settings.OAUTH2['SCOPE']
        }, request=request)

        registrar_log(request.session.get('current_payment_id', "SIN_ID"), tipo_log='AUTH', extra_info="Token OAuth2 almacenado en sesión exitosamente")

        messages.success(request, "Autorización completada exitosamente!")
        return render(request, 'api/GPT4/oauth2_callback.html')

    except Exception as e:
        registrar_log_oauth("callback", "error", None, str(e), request=request)
        registrar_log(str(Transfer.payment_id), tipo_log="ERROR", error=str(e), extra_info="Excepción en oauth2_callback")
        request.session['oauth_success'] = False
        messages.error(request, f"Error en el proceso de autorización: {str(e)}")
        return render(request, 'api/GPT4/oauth2_callback.html')


def get_oauth_logs(request):

    session_key = request.GET.get('session_key')
    if not session_key:
        return JsonResponse({'error': 'Session key required'}, status=400)

    archivo_path = os.path.join(BASE_SCHEMA_DIR, "oauth_logs", f"oauth_general.log")
    logs_archivo = []
    logs_bd = []

    if os.path.exists(archivo_path):
        try:
            with open(archivo_path, 'r') as f:
                logs_archivo = [json.loads(line) for line in f.readlines()]
        except Exception as e:
            logs_archivo = [f"Error leyendo archivo: {e}"]

    try:
        logs_bd_qs = LogTransferencia.objects.filter(registro=session_key).order_by('-created_at')
        logs_bd = [{
            "fecha": log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "tipo_log": log.tipo_log,
            "contenido": log.contenido
        } for log in logs_bd_qs]
    except Exception as e:
        logs_bd = [f"Error leyendo base de datos: {e}"]

    return JsonResponse({
        'session_key': session_key,
        'logs_archivo': logs_archivo,
        'logs_bd': logs_bd
    })


@require_POST
def toggle_oauth(request):
    request.session['oauth_active'] = 'oauth_active' in request.POST
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def list_logs(request):
    registro = request.GET.get("registro", "").strip()
    tipo_log = request.GET.get("tipo_log", "").strip()

    logs = LogTransferencia.objects.all()

    if registro:
        logs = logs.filter(registro__icontains=registro)
    if tipo_log:
        logs = logs.filter(tipo_log__iexact=tipo_log)

    logs = logs.order_by('-created_at')[:500]
    choices = LogTransferencia._meta.get_field('tipo_log').choices

    return render(request, 'api/GPT4/list_logs.html', {
        "logs": logs,
        "registro": registro,
        "tipo_log": tipo_log,
        "choices": choices
    })
    



@csrf_exempt
def log_oauth_visual_inicio(request):
    if not request.session.session_key:
        request.session.save()  # Fuerza a crear una sesión si no existe

    payment_id = request.GET.get("payment_id") or request.session.get("current_payment_id", "SIN_ID")
    user_agent = request.META.get("HTTP_USER_AGENT", "Desconocido")
    ip_address = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "IP desconocida"))
    now = datetime.now(timezone.utc)

    metadata = {
        "payment_id": payment_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp_utc": now.isoformat(timespec='milliseconds').replace("+00:00", "Z"),
        "timestamp_unix_ms": int(now.timestamp() * 1000),
        "session_id": request.session.session_key
    }

    registrar_log_oauth(
        accion="AUTORIZACION_VISUAL_INICIADA",
        estado="ok",
        metadata=metadata,
        request=request
    )
    return JsonResponse({"status": "RJCT"})


def send_transfer_view(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
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
                send_transfer(transfer, final_token, otp)
                registrar_log(transfer.payment_id, tipo_log='TRANSFER', extra_info="Transferencia enviada correctamente")
                request.session.pop('access_token', None)
                request.session.pop('refresh_token', None)
                request.session.pop('token_expires', None)
                request.session.pop('oauth_success', None)
                request.session.pop('current_payment_id', None)
                messages.success(request, "Transferencia enviada correctamente.")
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            
            except Exception as e:
                
                registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error enviando transferencia")
                messages.error(request, str(e))
                return redirect('transfer_detailGPT4', payment_id=payment_id)

        except Exception as e:
            registrar_log(transfer.payment_id, tipo_log='ERROR', error=str(e), extra_info="Error inesperado en vista")
            messages.error(request, f"Error inesperado: {str(e)}")
            return redirect('transfer_detailGPT4', payment_id=payment_id)

    return render(request, "gpt4/send_transfer.html", {"form": form, "transfer": transfer})


@requiere_conexion_banco
def send_transfer_gateway_view(request, payment_id):
    """Unified view to handle connection, simulator and fake modes."""
    mode = request.GET.get("mode") or "conexion"
    transfer = get_object_or_404(Transfer, payment_id=payment_id)

    if mode == "fake":
        if not get_settings()["ALLOW_FAKE_BANK"]:
            return HttpResponseForbidden("Modo simulado desactivado")
        if request.method == "POST":
            transfer.status = "ACSP"
            transfer.save()
            registrar_log(payment_id, tipo_log="TRANSFER", extra_info="Transferencia simulada completada")
            return JsonResponse({"status": transfer.status})
        return render(request, "api/GPT4/send_transfer.html", {"transfer": transfer})

    if mode == "simulator":
        form = SendTransferForm(request.POST or None)
        settings_data = banco_settings()
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

        if request.method == "POST" and form.is_valid():
            otp = form.cleaned_data['otp']
            token = request.session.get('sim_token')
            if not token:
                messages.error(request, "Token de simulador no disponible.")
                return redirect('send_transfer_gateway_viewGPT4', payment_id=payment_id, mode='simulator')
            try:
                enviar_transferencia_conexion(request, transfer, token, otp)
                if transfer.status == 'PDNG':
                    wait_for_final_status(transfer, token)
                messages.success(request, "Transferencia enviada correctamente.")
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                messages.error(request, str(e))
                return redirect('transfer_detailGPT4', payment_id=payment_id)

        return render(request, "api/GPT4/send_transfer.html", {
            "form": form,
            "transfer": transfer,
            "ip_simulator": ip_sim,
        })

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
                if transfer.status == 'PDNG':
                    wait_for_final_status(transfer, final_token)
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

    return render(request, "api/GPT4/send_transfer.html", {"form": form, "transfer": transfer})

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
from django.shortcuts import render
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






