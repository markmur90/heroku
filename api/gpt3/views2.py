import logging
import os
import uuid
import json
import requests
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from api.core.services import generar_pdf_transferencia
from api.gpt3.helpers import generate_deterministic_id, generate_payment_id_uuid, obtener_ruta_schema_transferencia
from api.gpt3.utils2 import generar_otp_sepa_transfer, get_oauth_session, guardar_pain002_si_aplica, handle_error_response, preparar_payload_transferencia, registrar_log
from api.gpt3.schemas import sepa_credit_transfer_schema
from api.gpt4.utils import read_log_file
from .models import SepaCreditTransfer, PaymentIdentification, BulkTransfer, Address, Debtor, Creditor, FinancialInstitution, InstructedAmount
from .forms import SepaCreditTransferForm, AccountForm, AddressForm, PaymentIdentificationForm, DebtorForm, CreditorForm, FinancialInstitutionForm, InstructedAmountForm, BulkTransferForm, GroupHeaderForm, PaymentInformationForm
from config import settings

logger = logging.getLogger(__name__)

ORIGIN = settings.ORIGIN
API_URL = settings.API_URL

HEADERS_DEFAULT = {
    "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "es-CO",
    "Connection": "keep-alive",
    "Host": "api.db.com",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Origin": ORIGIN,
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
}

@login_required
def crear_transferencia(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generate_payment_id_uuid()
            transferencia.auth_id = generate_payment_id_uuid()
            transferencia.transaction_status = "PDNG"
            payment_identification = PaymentIdentification.objects.create(
                instruction_id=generate_deterministic_id(
                    transferencia.payment_id,
                    transferencia.creditor_account.iban,
                    transferencia.debtor_account.iban,
                ),
                end_to_end_id=generate_deterministic_id(
                    transferencia.payment_id,
                    transferencia.creditor_account.iban,
                    transferencia.debtor_account.iban,
                    transferencia.instructed_amount.amount,
                    transferencia.requested_execution_date,
                    prefix="E2E",
                ),
            )
            transferencia.payment_identification = payment_identification
            transferencia.save()
            try:
                from .generate_xml import generar_xml_pain001
                from .generate_aml import generar_archivo_aml
                generar_xml_pain001(transferencia, transferencia.payment_id)
                generar_archivo_aml(transferencia, transferencia.payment_id)
            except Exception as e:
                registrar_log(transferencia.payment_id, {}, error=f"Error generación inicial: {str(e)}")
                form.add_error(None, f"Error generando XML o AML: {str(e)}")
                messages.error(request, "Se produjo un error generando los esquemas. Corrige e intenta de nuevo.")
                return render(request, 'api/GPT3/crear_transferencia.html', {'form': form, 'transferencia': None})
            messages.success(request, "Transferencia creada correctamente.")
            return redirect('dashboard')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = SepaCreditTransferForm()
    return render(request, 'api/GPT3/crear_transferencia.html', {'form': form, 'transferencia': None})


@login_required
def listar_transferencias(request):
    transferencias = SepaCreditTransfer.objects.all().order_by('-created_at')
    paginator = Paginator(transferencias, 10)
    page = request.GET.get('page', 1)
    try:
        transferencias_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        transferencias_paginated = paginator.page(1)
    return render(request, 'api/GPT3/listar_transferencias.html', {'transferencias': transferencias_paginated})

@login_required
def detalle_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    # Lectura de logs
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    archivos_logs = {
        archivo: os.path.join(carpeta, archivo)
        for archivo in os.listdir(carpeta)
        if archivo.endswith(".log")
    }
    log_files_content = {}
    mensaje_error = None
    for nombre, ruta in archivos_logs.items():
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                log_files_content[nombre] = contenido
                if "=== Error ===" in contenido:
                    mensaje_error = contenido.split("=== Error ===")[-1].strip().split("===")[0].strip()
    # Lectura de XML/AML en memoria
    archivos = {}
    for key, filename in [
        ('pain001', f"pain001_{payment_id}.xml"),
        ('aml', f"aml_{payment_id}.xml"),
        ('pain002', f"pain002_{payment_id}.xml"),
    ]:
        path = os.path.join(carpeta, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                archivos[key] = f.read()
        else:
            archivos[key] = None
    # Detección adicional de errores en logs
    errores_detectados = []
    for contenido in log_files_content.values():
        if "Error" in contenido or "Traceback" in contenido or "no válido según el XSD" in contenido:
            errores_detectados.append(contenido)
    return render(request, 'api/GPT3/detalle_transferencia.html', {
        'transferencia': transferencia,
        'log_files_content': log_files_content,
        'archivos': archivos,
        'mensaje_error': mensaje_error,
        'errores_detectados': errores_detectados,
    })


@login_required
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    otp_token = generar_otp_sepa_transfer()
    if not otp_token:
        messages.error(request, "No se pudo generar el OTP.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {get_oauth_session(request).token['access_token']}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
        "otp": otp_token,
    })
    try:
        payload = preparar_payload_transferencia(transferencia, request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
    try:
        response = requests.post(f"{API_URL}/", json=payload, headers=headers, timeout=(5, 15))
        registrar_log(payment_id, headers, response.text)
        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            # transferencia.transaction_status = "ERRO"
            # transferencia.save()
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        respuesta_json = response.json()
        transferencia.transaction_status = respuesta_json.get('transactionStatus', 'PDNG')
        transferencia.save()
        guardar_pain002_si_aplica(response, payment_id)
        messages.success(request, "Transferencia enviada correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        # transferencia.transaction_status = "ERRO"
        # transferencia.save()
        messages.error(request, f"Error interno al enviar: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def estado_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        response = requests.get(f"{API_URL}/{payment_id}", headers=headers, timeout=(5, 15))
        registrar_log(payment_id, headers, response.text)
        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al consultar estado: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        respuesta_json = response.json()
        nueva_estado = respuesta_json.get("transactionStatus")
        if nueva_estado:
            transferencia.transaction_status = nueva_estado
            transferencia.save()
        guardar_pain002_si_aplica(response, payment_id)
        messages.success(request, "Estado actualizado correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al consultar estado: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def cancelar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp = generar_otp_sepa_transfer()
    if not otp:
        messages.error(request, "No se pudo obtener el OTP para cancelar.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
        'otp': otp,
    })
    try:
        response = requests.delete(f"{API_URL}/{payment_id}", headers=headers, timeout=(5, 15))
        registrar_log(payment_id, headers, response.text)
        if response.status_code not in [200, 204]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al cancelar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        transferencia.transaction_status = "CANC"
        transferencia.save()
        messages.success(request, "Transferencia cancelada correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al cancelar: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@login_required
def retry_second_factor_view(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp_token = generar_otp_sepa_transfer()
    if not otp_token:
        messages.error(request, "No se pudo obtener OTP para reintentar.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",

        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
        
        "otp": otp_token,
        
    })
    payload = {"action": "CREATE", "authId": transferencia.auth_id}
    try:
        response = requests.patch(f"{API_URL}/{payment_id}", headers=headers, json=payload, timeout=(5, 15))
        registrar_log(payment_id, headers, response.text)
        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al reintentar autenticación: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        guardar_pain002_si_aplica(response, payment_id)
        messages.success(request, "Reintento de autenticación completado correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al reintentar segundo factor: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@login_required
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente.")
            return redirect('account_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = AccountForm()
    return render(request, 'api/GPT3/create_account.html', {'form': form})

@login_required
def create_amount(request):
    if request.method == 'POST':
        form = InstructedAmountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Monto creado correctamente.")
            return redirect('amount_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = InstructedAmountForm()
    return render(request, 'api/GPT3/create_amount.html', {'form': form})

@login_required
def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Institución financiera creada correctamente.")
            return redirect('financial_institution_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT3/create_financial_institution.html', {'form': form})

@login_required
def create_postal_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Dirección postal creada correctamente.")
            return redirect('postal_address_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = AddressForm()
    return render(request, 'api/GPT3/create_postal_address.html', {'form': form})

@login_required
def create_payment_identification(request):
    if request.method == 'POST':
        form = PaymentIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Identificación de pago creada correctamente.")
            return redirect('dashboard')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = PaymentIdentificationForm()
    return render(request, 'api/GPT3/create_payment_identification.html', {'form': form})

@login_required
def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Deudor creado correctamente.")
            return redirect('debtor_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = DebtorForm()
    return render(request, 'api/GPT3/create_debtor.html', {'form': form})

@login_required
def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Acreedor creado correctamente.")
            return redirect('creditor_listGPT3')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = CreditorForm()
    return render(request, 'api/GPT3/create_creditor.html', {'form': form})



@login_required
def account_list_view(request):
    accounts = SepaCreditTransfer.objects.none()  # Ajusta según el modelo real
    paginator = Paginator(accounts, 10)
    page = request.GET.get('page', 1)
    try:
        accounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        accounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/account_list.html', {'accounts': accounts_paginated})

@login_required
def amount_list_view(request):
    amounts = InstructedAmount.objects.all().order_by('-id')
    paginator = Paginator(amounts, 10)
    page = request.GET.get('page', 1)
    try:
        amounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        amounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/amount_list.html', {'amounts': amounts_paginated})

@login_required
def financial_institution_list_view(request):
    institutions = FinancialInstitution.objects.all().order_by('-id')
    paginator = Paginator(institutions, 10)
    page = request.GET.get('page', 1)
    try:
        institutions_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        institutions_paginated = paginator.page(1)
    return render(request, 'api/GPT3/financial_institution_list.html', {'institutions': institutions_paginated})

@login_required
def postal_address_list_view(request):
    addresses = Address.objects.all().order_by('-id')
    paginator = Paginator(addresses, 10)
    page = request.GET.get('page', 1)
    try:
        addresses_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        addresses_paginated = paginator.page(1)
    return render(request, 'api/GPT3/postal_address_list.html', {'addresses': addresses_paginated})

@login_required
def debtor_list_view(request):
    debtors = Debtor.objects.all().order_by('-id')
    paginator = Paginator(debtors, 10)
    page = request.GET.get('page', 1)
    try:
        debtors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        debtors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/debtor_list.html', {'debtors': debtors_paginated})

@login_required
def creditor_list_view(request):
    creditors = Creditor.objects.all().order_by('-id')
    paginator = Paginator(creditors, 10)
    page = request.GET.get('page', 1)
    try:
        creditors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        creditors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/creditor_list.html', {'creditors': creditors_paginated})



@login_required
def listar_bulk_transferencias(request):
    bulk_transfers = BulkTransfer.objects.all().order_by('-created_at')
    paginator = Paginator(bulk_transfers, 10)
    page = request.GET.get('page', 1)
    try:
        bulk_transfers_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        bulk_transfers_paginated = paginator.page(1)
    return render(request, 'api/GPT3/listar_bulk.html', {'bulk_transfers': bulk_transfers_paginated})

@login_required
class CrearBulkTransferView(View):
    def get(self, request):
        bulk_form = BulkTransferForm()
        group_form = GroupHeaderForm()
        payment_info_form = PaymentInformationForm()
        return render(request, 'api/GPT3/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })
    def post(self, request):
        bulk_form = BulkTransferForm(request.POST)
        group_form = GroupHeaderForm(request.POST)
        payment_info_form = PaymentInformationForm(request.POST)
        if bulk_form.is_valid() and group_form.is_valid() and payment_info_form.is_valid():
            bulk = bulk_form.save(commit=False)
            bulk.payment_id = generate_payment_id_uuid()
            bulk.transaction_status = "PDNG"
            bulk.save()
            carpeta = obtener_ruta_schema_transferencia(bulk.payment_id)
            os.makedirs(carpeta, exist_ok=True)
            with open(os.path.join(carpeta, f"pain001_bulk_{bulk.payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{bulk.payment_id}</PaymentID></BulkTransfer>")
            with open(os.path.join(carpeta, f"aml_bulk_{bulk.payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"AML info for bulk transfer {bulk.payment_id}\n")
            messages.success(request, "Transferencia masiva creada correctamente.")
            return redirect('listar_bulkGPT3')
        messages.error(request, "Por favor corrige los errores en el formulario.")
        return render(request, 'api/GPT3/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })

@login_required
class EnviarBulkTransferView(View):
    def get(self, request, payment_id):
        try:
            carpeta = obtener_ruta_schema_transferencia(payment_id)
            with open(os.path.join(carpeta, f"pain001_bulk_{payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{payment_id}</PaymentID><Status>Pending</Status></BulkTransfer>")
            with open(os.path.join(carpeta, f"aml_bulk_{payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"AML actualizado para {payment_id}\n")
            registro = f"<Response><Reference>{payment_id}</Reference><Status>Recibido</Status></Response>"
            registrar_log(payment_id, {"Operacion": "Envio Bulk Simulado"}, registro)
            bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
            bulk.transaction_status = "PDNG"
            bulk.save()
            messages.success(request, f"Transferencia masiva {payment_id} enviada y registrada.")
        except Exception as e:
            registrar_log(payment_id, {"Operacion": "Error Envio Bulk"}, error=str(e))
            messages.error(request, f"Error al enviar transferencia masiva: {str(e)}")
        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)

@login_required
class EstadoBulkTransferView(View):
    def get(self, request, payment_id):
        try:
            carpeta = obtener_ruta_schema_transferencia(payment_id)
            estado_xml = f"<StatusResponse><Reference>{payment_id}</Reference><Status>Procesando</Status></StatusResponse>"
            with open(os.path.join(carpeta, f"pain002_bulk_{payment_id}_estado.xml"), 'w', encoding='utf-8') as xml:
                xml.write(estado_xml)
            registrar_log(payment_id, {"Operacion": "Consulta Estado Bulk Simulado"}, estado_xml)
            bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
            bulk.transaction_status = "PROC"
            bulk.save()
            messages.success(request, "Estado de transferencia masiva actualizado correctamente.")
        except Exception as e:
            registrar_log(payment_id, {"Operacion": "Error Consulta Estado Bulk"}, error=str(e))
            messages.error(request, f"Error al consultar estado de bulk: {str(e)}")
        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)


@login_required
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    generar_pdf_transferencia(transferencia)
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    pdf_archivo = next(
        (os.path.join(carpeta_transferencia, f) for f in os.listdir(carpeta_transferencia)
         if f.endswith(".pdf") and payment_id in f),
        None
    )

    if not pdf_archivo or not os.path.exists(pdf_archivo):
        messages.error(request, "El archivo PDF no se encuentra disponible.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    return FileResponse(open(pdf_archivo, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_archivo))