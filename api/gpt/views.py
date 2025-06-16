import uuid
import logging
import re

from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseServerError, JsonResponse

from api.gpt.models import SepaCreditTransfer, ErrorResponse, PaymentIdentification, PostalAddress, Debtor, Creditor, Account, FinancialInstitution, Amount

from api.gpt.helpers import generate_payment_id, generate_deterministic_id

from api.gpt.utils import generar_pdf_transferencia, validate_headers, build_headers, attach_common_headers, handle_error_response, generate_sepa_json_payload, get_oauth_session, validate_parameters

from api.gpt.forms import AccountForm, AmountForm, FinancialInstitutionForm,PostalAddressForm, PaymentIdentificationForm, DebtorForm, CreditorForm, SepaCreditTransferForm

logger = logging.getLogger(__name__)

# Token de acceso dummy (debería obtenerse con autenticación OAuth real)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

API_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
API_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'
DEUTSCHE_BANK_CLIENT_ID='SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
DEUTSCHE_BANK_CLIENT_SECRET='H858hfhg0ht40588hhfjpfhhd9944940jf'

CLIENT_ID = API_CLIENT_ID
CLIENT_SECRET = API_CLIENT_SECRET

def generate_transfer_pdf(request, payment_id):
    """Genera un PDF para una transferencia específica"""
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    pdf_path = generar_pdf_transferencia(transfer)
    return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"{transfer.payment_id}.pdf")


@require_http_methods(["GET", "POST"])
def initiate_sepa_transfer(request):
    if request.method == 'POST':
        headers = {
            'idempotency-id': request.headers.get('idempotency-id', str(uuid.uuid4())),
            'process-id': request.headers.get('process-id'),
            'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
            'Correlation-ID': request.headers.get('Correlation-ID', str(uuid.uuid4())),
            'Origin': str(ORIGIN),
            'Accept': 'application/json',
            'X-Requested-With': request.headers.get('X-Requested-With'),
            'Content-Type': 'application/json',
            'Access-Control-Request-Method': request.headers.get('Access-Control-Request-Method'),
            'Access-Control-Request-Headers': request.headers.get('Access-Control-Request-Headers'),
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Cookie': request.headers.get('Cookie'),
            'X-Frame-Options': request.headers.get('X-Frame-Options'),
            'X-Content-Type-Options': request.headers.get('X-Content-Type-Options'),
            'Strict-Transport-Security': request.headers.get('Strict-Transport-Security'),
            'previewsignature': request.headers.get('previewsignature'),
        }

        # Construir cabeceras adicionales
        headers = build_headers(request, external_method='POST')
        
        validation_errors = validate_headers(headers)
        if validation_errors:
            return JsonResponse({'errors': validation_errors}, status=400)

        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            validation_errors = validate_parameters(request.POST)
            if validation_errors:
                return JsonResponse({'errors': validation_errors}, status=400)
            try:
                transfer = form.save(commit=False)
                transfer.payment_id = uuid.uuid4()
                transfer.auth_id = uuid.uuid4()
                transfer.transaction_status = 'PDNG'

                # Generar PaymentIdentification automáticamente
                transfer.payment_identification = PaymentIdentification.objects.create(
                    end_to_end_id=generate_payment_id(),
                    instruction_id=generate_deterministic_id(
                        transfer.creditor_account.iban,
                        transfer.instructed_amount.amount,
                        transfer.requested_execution_date
                    )
                )

                transfer.idempotency_key = headers['idempotency-id']  # Asignar idempotency_key
                transfer.save()

                payload = generate_sepa_json_payload(transfer)

                headers.update({
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {ACCESS_TOKEN}",
                    'X-Requested-With': 'XMLHttpRequest',  # Cabecera requerida
                    'Origin': str(ORIGIN),  # Cabecera requerida
                })

                headers = attach_common_headers(headers, external_method='POST')
                oauth = get_oauth_session(request)
                response = oauth.post(
                    'https://api.db.com:443/gw/dbapi/banking/transactions/v2',
                    json=payload, headers=headers
                )

                if response.status_code == 201:
                    return render(request, 'api/GPT/transfer_success.html', {
                        'payment_id': transfer.payment_id,
                        'execution_date': transfer.requested_execution_date,
                        'creditor': transfer.creditor.creditor_name,
                        'debtor': transfer.debtor.debtor_name,
                        'idempotency_id': transfer.idempotency_key
                    })
                else:
                    error_message = handle_error_response(response)
                    ErrorResponse.objects.create(
                        code=response.status_code,
                        message=error_message,
                        message_id=headers['idempotency-id']
                    )
                    return HttpResponseBadRequest(error_message)

            except Exception as e:
                ErrorResponse.objects.create(
                    code=500,
                    message=str(e),
                    message_id=headers.get('idempotency-id', '')
                )
                return HttpResponseServerError("Error interno del servidor")
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = SepaCreditTransferForm()

    return render(request, 'api/GPT/initiate_transfer.html', {'form': form})

def check_transfer_status(request, payment_id):
    try:
        # Validar que payment_id sea un UUID válido
        uuid.UUID(payment_id)

        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json',
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        }

        # Incluir Correlation-Id si está presente en la solicitud
        correlation_id = request.headers.get('Correlation-ID', str(uuid.uuid4()))
        if correlation_id:
            headers['Correlation-Id'] = correlation_id

        response = oauth.get(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}/status',
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            new_status = data.get('transactionStatus')
            if new_status:
                transfer.transaction_status = new_status
                transfer.save()
        else:
            error_message = handle_error_response(response)
            logger.warning(f"Error consultando estado: {error_message}")
            return HttpResponseBadRequest(error_message)

        return render(request, 'api/GPT/transfer_status.html', {
            'transfer': transfer,
            'bank_response': response.json() if response.ok else None
        })

    except ValueError:
        return HttpResponseBadRequest("El payment_id proporcionado no es un UUID válido.")
    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error consultando estado: {str(e)}"
        )
        return render(request, 'api/GPT/transfer_status.html', {
            'transfer': transfer,
            'error': str(e)
        })


@require_http_methods(["DELETE"])
def cancel_sepa_transfer(request, payment_id):
    headers = {
        'idempotency-id': request.headers.get('idempotency-id'),
        'otp': request.headers.get('otp'),
        'Correlation-Id': request.headers.get('Correlation-ID', str(uuid.uuid4())),
        'apikey': request.headers.get('apikey'),
        'process-id': request.headers.get('process-id'),
        'previewsignature': request.headers.get('previewsignature'),
        'Accept-Encoding': request.headers.get('Accept-Encoding'),
        'Accept-Language': request.headers.get('Accept-Language'),
        'Connection': request.headers.get('Connection'),
        'Priority': request.headers.get('Priority'),
        'Sec-Fetch-Dest': request.headers.get('Sec-Fetch-Dest'),
        'Sec-Fetch-Mode': request.headers.get('Sec-Fetch-Mode'),
        'Sec-Fetch-Site': request.headers.get('Sec-Fetch-Site'),
        'Sec-Fetch-User': request.headers.get('Sec-Fetch-User'),
        'Upgrade-Insecure-Requests': request.headers.get('Upgrade-Insecure-Requests'),
        'User-Agent': request.headers.get('User-Agent'),
    }

    # Validar cabeceras iniciales
    validation_errors = validate_headers(headers)
    if validation_errors:
        return JsonResponse({'errors': validation_errors}, status=400)

    # Construir cabeceras adicionales
    headers = build_headers(request, external_method='DELETE')
    validation_errors = validate_headers(headers)
    if validation_errors:
        return JsonResponse({'errors': validation_errors}, status=400)

    try:
        # Obtener la transferencia SEPA
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        # Obtener sesión OAuth
        oauth = get_oauth_session(request)

        # Actualizar cabeceras con información adicional
        headers.update({
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        })
        headers = attach_common_headers(headers, external_method='DELETE')

        # Realizar la solicitud DELETE a la API externa
        response = oauth.delete(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
            headers=headers
        )

        if response.status_code == 200:
            # Actualizar el estado de la transferencia a 'CANC'
            transfer.transaction_status = 'CANC'
            transfer.save()
            return render(request, 'api/GPT/cancel_success.html', {
                'transfer': transfer
            })
        else:
            # Manejar errores de la API externa
            error_message = handle_error_response(response)
            ErrorResponse.objects.create(
                code=response.status_code,
                message=error_message,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest(error_message)

    except Exception as e:
        # Manejar excepciones generales
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en cancelación: {str(e)}"
        )
        return HttpResponseServerError("Error cancelando la transferencia")


@require_http_methods(["POST"])
def retry_sepa_transfer_auth(request, payment_id):
    headers = {
        'idempotency-id': request.headers.get('idempotency-id'),
        'otp': request.headers.get('otp'),
        'Correlation-Id': request.headers.get('Correlation-ID', str(uuid.uuid4())),
        'apikey': request.headers.get('apikey'),
        'process-id': request.headers.get('process-id'),
        'previewsignature': request.headers.get('previewsignature'),
    }
    validation_errors = validate_headers(headers)
    if validation_errors:
        return JsonResponse({'errors': validation_errors}, status=400)

    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        # Validar que los campos 'action' y 'authId' estén presentes
        action = request.POST.get('action')
        auth_id = request.POST.get('authId')
        if not action or not auth_id:
            return JsonResponse({'errors': ["'action' y 'authId' son requeridos para reintentar el segundo factor."]}, status=400)

        oauth = get_oauth_session(request)
        headers.update({
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        })

        payload = {
            "action": action,
            "authId": auth_id
        }

        response = oauth.patch(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            return render(request, 'api/GPT/retry_success.html', {
                'transfer': transfer
            })
        else:
            error_message = handle_error_response(response)
            ErrorResponse.objects.create(
                code=response.status_code,
                message=error_message,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest(error_message)

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en retry auth: {str(e)}"
        )
        return HttpResponseServerError("Error en retry autenticación")


def transfer_list_view(request):
    """Listado de todas las transferencias con paginación"""
    transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    
    # Configurar paginación
    page = request.GET.get('page', 1)  # Obtener el número de página de la URL
    paginator = Paginator(transfers, 10)  # Mostrar 10 transferencias por página

    try:
        transfers_paginated = paginator.page(page)
    except PageNotAnInteger:
        transfers_paginated = paginator.page(1)  # Mostrar la primera página si el número de página no es válido
    except EmptyPage:
        transfers_paginated = paginator.page(paginator.num_pages)  # Mostrar la última página si el número es demasiado alto

    # Agregar información de estado para la plantilla
    for transfer in transfers_paginated:
        transfer.status_display = transfer.get_transaction_status_display()
        transfer.status_color = transfer.get_status_color()
    
    return render(request, 'api/GPT/transfer_list.html', {
        'transfers': transfers_paginated
    })


@require_http_methods(["DELETE"])
def delete_transfer(request, payment_id):
    """Elimina una transferencia SEPA por su payment_id."""
    # Validar que el payment_id sea un UUID válido
    try:
        uuid.UUID(payment_id)
    except ValueError:
        return HttpResponseBadRequest("El payment_id proporcionado no es un UUID válido.")

    try:
        transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
        transfer.delete()
        logger.info(f"Transferencia eliminada: {payment_id}")
        return redirect('api/GPT/transfer_list.html')  # Redirigir al listado de transferencias
    except SepaCreditTransfer.DoesNotExist:
        logger.error(f"Transferencia no encontrada: {payment_id}")
        return HttpResponseBadRequest("Transferencia no existe")
    except Exception as e:
        logger.exception("Error eliminando transferencia")
        return HttpResponseServerError("Error eliminando transferencia")


def cancel_success_view(request, payment_id):
    """Vista para mostrar éxito de cancelación."""
    return render(request, 'api/GPT/cancel_success.html', {'payment_id': payment_id})


def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_listGPT')
    else:
        form = AccountForm()
    return render(request, 'api/GPT/create_account.html', {'form': form})


def create_amount(request):
    if request.method == 'POST':
        form = AmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('amount_listGPT')
    else:
        form = AmountForm()
    return render(request, 'api/GPT/create_amount.html', {'form': form})


def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('financial_institution_listGPT')
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT/create_financial_institution.html', {'form': form})


def create_postal_address(request):
    if request.method == 'POST':
        form = PostalAddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('postal_address_listGPT')
    else:
        form = PostalAddressForm()
    return render(request, 'api/GPT/create_postal_address.html', {'form': form})


def create_payment_identification(request):
    if request.method == 'POST':
        form = PaymentIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
    else:
        form = PaymentIdentificationForm()
    return render(request, 'api/GPT/create_payment_identification.html', {'form': form})


def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('debtor_listGPT')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT/create_debtor.html', {'form': form})


def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('creditor_listGPT')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT/create_creditor.html', {'form': form})


def postal_address_list_view(request):
    addresses = PostalAddress.objects.all().order_by('-id')
    paginator = Paginator(addresses, 10)
    page = request.GET.get('page', 1)
    try:
        addresses_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        addresses_paginated = paginator.page(1)
    return render(request, 'api/GPT/postal_address_list.html', {'addresses': addresses_paginated})


def debtor_list_view(request):
    debtors = Debtor.objects.all().order_by('-id')
    paginator = Paginator(debtors, 10)
    page = request.GET.get('page', 1)
    try:
        debtors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        debtors_paginated = paginator.page(1)
    return render(request, 'api/GPT/debtor_list.html', {'debtors': debtors_paginated})


def creditor_list_view(request):
    creditors = Creditor.objects.all().order_by('-id')
    paginator = Paginator(creditors, 10)
    page = request.GET.get('page', 1)
    try:
        creditors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        creditors_paginated = paginator.page(1)
    return render(request, 'api/GPT/creditor_list.html', {'creditors': creditors_paginated})


def account_list_view(request):
    accounts = Account.objects.all().order_by('-id')
    paginator = Paginator(accounts, 10)
    page = request.GET.get('page', 1)
    try:
        accounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        accounts_paginated = paginator.page(1)
    return render(request, 'api/GPT/account_list.html', {'accounts': accounts_paginated})


def financial_institution_list_view(request):
    institutions = FinancialInstitution.objects.all().order_by('-id')
    paginator = Paginator(institutions, 10)
    page = request.GET.get('page', 1)
    try:
        institutions_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        institutions_paginated = paginator.page(1)
    return render(request, 'api/GPT/financial_institution_list.html', {'institutions': institutions_paginated})


def amount_list_view(request):
    amounts = Amount.objects.all().order_by('-id')
    paginator = Paginator(amounts, 10)
    page = request.GET.get('page', 1)
    try:
        amounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        amounts_paginated = paginator.page(1)
    return render(request, 'api/GPT/amount_list.html', {'amounts': amounts_paginated})

