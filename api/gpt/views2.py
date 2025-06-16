from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseServerError, JsonResponse
from .models import SepaCreditTransfer, ErrorResponse, PaymentIdentification, PostalAddress, Debtor, Creditor, Account, FinancialInstitution, Amount
from .forms import SepaCreditTransferForm
from .utils import get_oauth_session, generate_sepa_json_payload, validate_parameters
import uuid
import logging
from .helpers import generate_payment_id, generate_deterministic_id
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import FileResponse
from .utils import generar_pdf_transferencia
from .forms import (
    AccountForm, AmountForm, FinancialInstitutionForm,
    PostalAddressForm, PaymentIdentificationForm, DebtorForm, CreditorForm
)
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
import re
from datetime import datetime

logger = logging.getLogger(__name__)

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

API_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
API_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'
DEUTSCHE_BANK_CLIENT_ID='SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
DEUTSCHE_BANK_CLIENT_SECRET='H858hfhg0ht40588hhfjpfhhd9944940jf'

CLIENT_ID = API_CLIENT_ID
CLIENT_SECRET = API_CLIENT_SECRET

def validate_headers(headers):
    """Valida las cabeceras requeridas para las solicitudes."""
    errors = []
    idempotency_id = headers.get('idempotency-id', '')
    
    if not isinstance(idempotency_id, str):
        idempotency_id = str(idempotency_id)  # Asegurarse de que sea una cadena
        
    if 'idempotency-id' not in headers or not re.match(r'^[a-f0-9\-]{36}$', idempotency_id):
        errors.append("Cabecera 'idempotency-id' es requerida y debe ser un UUID válido.")
        
    if 'otp' not in headers or not headers.get('otp'):
        errors.append("Cabecera 'otp' es requerida.")
        
    correlation_id = headers.get('Correlation-Id')
    if correlation_id is not None and len(correlation_id) > 50:
        errors.append("Cabecera 'Correlation-Id' no debe exceder los 50 caracteres.")
        
    if 'apikey' not in headers or not headers.get('apikey'):
        errors.append("Cabecera 'apikey' es requerida.")
        
    if 'process-id' in headers and not headers.get('process-id'):
        errors.append("Cabecera 'process-id' no debe estar vacía si está presente.")
        
    if 'previewsignature' in headers and not headers.get('previewsignature'):
        errors.append("Cabecera 'previewsignature' no debe estar vacía si está presente.")
        
    if 'access-control-allow-origin' not in headers:
        errors.append("Cabecera 'access-control-allow-origin' es requerida.")
        
    if 'access-control-allow-methods' in headers and not headers.get('access-control-allow-methods'):
        errors.append("Cabecera 'access-control-allow-methods' es requerida.")
        
    if 'access-control-allow-headers' in headers and not headers.get('access-control-allow-headers'):
        errors.append("Cabecera 'access-control-allow-headers' es requerida.")
        
    if 'x-request-id' not in headers or not re.match(r'^[a-f0-9\-]{36}$', headers.get('x-request-id', '')):
        errors.append("Cabecera 'x-request-id' es requerida y debe ser un UUID válido.")
        
    return errors





def handle_error_response(response):
    """Maneja los códigos de error específicos de la API."""
    error_messages = {
        2: "Valor inválido para uno de los parámetros.",
        16: "Respuesta de desafío OTP inválida.",
        17: "OTP inválido.",
        114: "No se pudo identificar la transacción por Id.",
        127: "La fecha de reserva inicial debe preceder a la fecha de reserva final.",
        131: "Valor inválido para 'sortBy'. Valores válidos: 'bookingDate[ASC]' y 'bookingDate[DESC]'.",
        132: "No soportado.",
        138: "Parece que inició un desafío no pushTAN. Use el endpoint PATCH para continuar.",
        139: "Parece que inició un desafío pushTAN. Use el endpoint GET para continuar.",
        6500: "Parámetros en la URL o tipo de contenido incorrectos. Por favor, revise y reintente.",
        6501: "Detalles del banco contratante inválidos o faltantes.",
        6502: "La moneda aceptada para el monto instruido es EUR. Por favor, corrija su entrada.",
        6503: "Parámetros enviados son inválidos o faltantes.",
        6504: "Los parámetros en la solicitud no coinciden con la solicitud inicial.",
        6505: "Fecha de ejecución inválida.",
        6506: "El IdempotencyId ya está en uso.",
        6507: "No se permite la cancelación para esta transacción.",
        6508: "Pago SEPA no encontrado.",
        6509: "El parámetro en la solicitud no coincide con el último Auth id.",
        6510: "El estado actual no permite la actualización del segundo factor con la acción proporcionada.",
        6511: "Fecha de ejecución inválida.",
        6515: "El IBAN de origen o el tipo de cuenta son inválidos.",
        6516: "No se permite la cancelación para esta transacción.",
        6517: "La moneda aceptada para la cuenta del acreedor es EUR. Por favor, corrija su entrada.",
        6518: "La fecha de recolección solicitada no debe ser un día festivo o fin de semana. Por favor, intente nuevamente.",
        6519: "La fecha de ejecución solicitada no debe ser mayor a 90 días en el futuro. Por favor, intente nuevamente.",
        6520: "El valor de 'requestedExecutionDate' debe coincidir con el formato yyyy-MM-dd.",
        6521: "La moneda aceptada para la cuenta del deudor es EUR. Por favor, corrija su entrada.",
        6523: "No hay una entidad legal presente para el IBAN de origen. Por favor, corrija su entrada.",
        6524: "Ha alcanzado el límite máximo permitido para el día. Espere hasta mañana o reduzca el monto de la transferencia.",
        6525: "Por el momento, no soportamos photo-tan para pagos masivos.",
        6526: "El valor de 'createDateTime' debe coincidir con el formato yyyy-MM-dd'T'HH:mm:ss.",
        401: "La función solicitada requiere un nivel de autenticación SCA.",
        404: "No se encontró el recurso solicitado.",
        409: "Conflicto: El recurso ya existe o no se puede procesar la solicitud."
    }
    error_code = response.status_code
    return error_messages.get(error_code, f"Error desconocido: {response.text}")


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
            'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
            'Correlation-Id': request.headers.get('Correlation-Id', str(uuid.uuid4())),
            'apikey': request.headers.get('apikey'),
            'Access-Control-Request-Method': request.headers.get('Access-Control-Request-Method'),
            'Access-Control-Request-Headers': request.headers.get('Access-Control-Request-Headers'),
            'x-request-id': request.headers.get('x-request-id', str(uuid.uuid4())),
            'Cookie': request.headers.get('Cookie'),
            'X-Frame-Options': request.headers.get('X-Frame-Options'),
            'X-Content-Type-Options': request.headers.get('X-Content-Type-Options'),
            'Strict-Transport-Security': request.headers.get('Strict-Transport-Security'),
            'Accept': 'application/json'
        }
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
                
                transfer.idempotency_key = headers['idempotency-id']
                transfer.save()

                payload = generate_sepa_json_payload(transfer)

                headers.update({
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {ACCESS_TOKEN}",
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': str(ORIGIN),
                })

                oauth = get_oauth_session(request)
                response = oauth.post(
                    'https://api.db.com:443/gw/dbapi/banking/transactions/v2',
                    json=payload,
                    headers=headers
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
        correlation_id = request.headers.get('Correlation-Id')
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
        'Correlation-Id': request.headers.get('Correlation-Id'),
        'apikey': request.headers.get('apikey'),
        'process-id': request.headers.get('process-id'),
        'previewsignature': request.headers.get('previewsignature'),
    }
    validation_errors = validate_headers(headers)
    if validation_errors:
        return JsonResponse({'errors': validation_errors}, status=400)

    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers.update({
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        })

        response = oauth.delete(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
            headers=headers
        )

        if response.status_code == 200:
            transfer.transaction_status = 'CANC'
            transfer.save()
            return render(request, 'api/GPT/cancel_success.html', {
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
            message=f"Error en cancelación: {str(e)}"
        )
        return HttpResponseServerError("Error cancelando la transferencia")


@require_http_methods(["POST"])
def retry_sepa_transfer_auth(request, payment_id):
    headers = {
        'idempotency-id': request.headers.get('idempotency-id'),
        'otp': request.headers.get('otp'),
        'Correlation-Id': request.headers.get('Correlation-Id'),
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

