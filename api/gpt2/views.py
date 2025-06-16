from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseServerError
from .models import SepaCreditTransfer, ErrorResponse, PaymentIdentification
from .forms import SepaCreditTransferForm
from .utils import get_oauth_session, generate_sepa_json_payload
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

logger = logging.getLogger(__name__)

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'

CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'


def generate_transfer_pdf(request, payment_id):
    """Genera un PDF para una transferencia específica"""
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    pdf_path = generar_pdf_transferencia(transfer)
    return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"{transfer.payment_id}.pdf")


@require_http_methods(["GET", "POST"])
def initiate_sepa_transfer(request):
    if request.method == 'POST':
        headers = {
            'idempotency-id': str(uuid.uuid4()),  # Generar idempotency_key automáticamente
            'Accept': 'application/json'
        }
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                transfer = form.save(commit=False)
                transfer.payment_id = uuid.uuid4()
                transfer.auth_id = uuid.uuid4()
                transfer.transaction_status = 'PDNG'
                
                # Generar PaymentIdentification automáticamente
                transfer.payment_identification = PaymentIdentification.objects.create(
                    end_to_end_id=generate_payment_id("E2E"),
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
                    'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
                    'Correlation-ID': str(uuid.uuid4()),
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
                        'idempotency_key': transfer.idempotency_key
                    })
                else:
                    ErrorResponse.objects.create(
                        code=response.status_code,
                        message=response.text,
                        message_id=headers['idempotency-id']
                    )
                    return HttpResponseBadRequest("Error en la operación bancaria")

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
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json',
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        }

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
            logger.warning(f"Respuesta no exitosa del banco: {response.status_code} - {response.text}")

        return render(request, 'api/GPT/transfer_status.html', {
            'transfer': transfer,
            'bank_response': response.json() if response.ok else None
        })

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error consultando estado: {str(e)}"
        )
        return render(request, 'api/GPT/transfer_status.html', {
            'transfer': transfer,
            'error': str(e)
        })


@require_http_methods(["POST"])
def cancel_sepa_transfer(request, payment_id):
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        }

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
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest("No se pudo cancelar la transferencia.")

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en cancelación: {str(e)}"
        )
        return HttpResponseServerError("Error cancelando la transferencia")


@require_http_methods(["POST"])
def retry_sepa_transfer_auth(request, payment_id):
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {ACCESS_TOKEN}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': str(ORIGIN),
        }

        payload = {
            "requestType": "SEPA_TRANSFER_GRANT"
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
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest("Error al reintentar la autenticación")

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
            return redirect('initiate_transferGPT')
    else:
        form = AccountForm()
    return render(request, 'api/GPT/create_account.html', {'form': form})


def create_amount(request):
    if request.method == 'POST':
        form = AmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
    else:
        form = AmountForm()
    return render(request, 'api/GPT/create_amount.html', {'form': form})


def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT/create_financial_institution.html', {'form': form})


def create_postal_address(request):
    if request.method == 'POST':
        form = PostalAddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
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
            return redirect('initiate_transferGPT')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT/create_debtor.html', {'form': form})


def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT/create_creditor.html', {'form': form})

