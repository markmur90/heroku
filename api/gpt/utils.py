import logging
import uuid
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from requests_oauthlib import OAuth2Session
from django.conf import settings

from api.gpt.models import SepaCreditTransfer
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


# Configuración OAuth2
OAUTH_CONFIG = {
    'client_id': str(CLIENT_ID),
    'client_secret': str(CLIENT_SECRET),
    'token_url': 'https://api.db.com/gw/oidc/token',
    'authorization_url': 'https://api.db.com/gw/oidc/authorize',
    'scopes': ['sepa_credit_transfers']
}

def get_oauth_session(request):
    """Crea sesión OAuth2 utilizando el access_token del entorno"""
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN no está configurado en las variables de entorno")
        raise ValueError("ACCESS_TOKEN no está configurado")

    # Crear sesión OAuth2 con el token de acceso
    return OAuth2Session(client_id=OAUTH_CONFIG['client_id'], token={'access_token': ACCESS_TOKEN, 'token_type': 'Bearer'})


def generate_sepa_json_payload(transfer):
    """Genera el JSON de transferencia SEPA según especificación del banco"""
    return {
        "creditor": {
            "name": transfer.creditor.creditor_name,
            "account": {
                "iban": transfer.creditor_account.iban,
                "currency": transfer.creditor_account.currency
            },
            "agent": {
                "bic": transfer.creditor_agent.financial_institution_id if transfer.creditor_agent else None
            },
            "address": {
                "country": transfer.creditor.postal_address.country,
                "zipCodeAndCity": transfer.creditor.postal_address.zip_code_and_city,
                "streetAndHouseNumber": transfer.creditor.postal_address.street_and_house_number
            }
        },
        "debtor": {
            "name": transfer.debtor.debtor_name,
            "account": {
                "iban": transfer.debtor_account.iban,
                "currency": transfer.debtor_account.currency
            },
            "address": {
                "country": transfer.debtor.postal_address.country,
                "zipCodeAndCity": transfer.debtor.postal_address.zip_code_and_city,
                "streetAndHouseNumber": transfer.debtor.postal_address.street_and_house_number
            }
        },
        "amount": {
            "currency": transfer.instructed_amount.currency,
            "amount": str(transfer.instructed_amount.amount)
        },
        "remittanceInformationUnstructured": transfer.remittance_information_unstructured,
        "requestedExecutionDate": transfer.requested_execution_date.strftime('%Y-%m-%d'),
        "endToEndId": transfer.payment_identification.end_to_end_id,
        "instructionId": transfer.payment_identification.instruction_id,
        "purposeCode": transfer.purpose_code,
        "priority": "High"  # Agregar prioridad (Instant SEPA Credit Transfer)
    }



import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import os
logger = logging.getLogger("bank_services")


def generar_pdf_transferencia(transfers):
    """
    Generates a well-organized PDF with SEPA transfer details.
    """
    # PDF file name
    creditor_name = transfers.creditor.creditor_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transfers.payment_id
    pdf_filename = f"{creditor_name}_{timestamp}_{payment_reference}.pdf"
    pdf_path = os.path.join("media", pdf_filename)

    # Create the media folder if it doesn't exist
    os.makedirs("media", exist_ok=True)

    # Create the PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(150, 750, "SEPA Transfer Receipt")  # Adjust title position
    c.setFont("Helvetica", 10)

    # Adjust initial positions
    current_y = 650  # Initial position for tables

    # Header
    header_data = [
        ["Creation Date", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
        ["Payment Reference", transfers.payment_id],
        ["Idempotency Key", transfers.idempotency_id]
    ]
    header_table = Table(header_data, colWidths=[150, 300])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    header_table.wrapOn(c, 50, current_y)
    header_table.drawOn(c, 50, current_y)
    current_y -= 120  # Adjust space for the next table

    # Debtor Information
    debtor_data = [
        ["Debtor Information", ""],
        ["Name", transfers.debtor.debtor_name],
        ["IBAN", transfers.debtor_account.iban],
        ["BIC", transfers.debtor_account.currency],  # No hay campo BIC en Account, se usa currency
        ["Address", f"{transfers.debtor.postal_address.street_and_house_number}, "
                    f"{transfers.debtor.postal_address.zip_code_and_city}, {transfers.debtor.postal_address.country}"]
    ]
    debtor_table = Table(debtor_data, colWidths=[150, 300])
    debtor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    debtor_table.wrapOn(c, 50, current_y)
    debtor_table.drawOn(c, 50, current_y)
    current_y -= 120  # Adjust space for the next table

    # Creditor Information
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transfers.creditor.creditor_name],
        ["IBAN", transfers.creditor_account.iban],
        ["BIC", transfers.creditor_account.currency],  # No hay campo BIC en Account, se usa currency
        ["Address", f"{transfers.creditor.postal_address.street_and_house_number}, "
                    f"{transfers.creditor.postal_address.zip_code_and_city}, {transfers.creditor.postal_address.country}"]
    ]
    creditor_table = Table(creditor_data, colWidths=[150, 300])
    creditor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    creditor_table.wrapOn(c, 50, current_y)
    creditor_table.drawOn(c, 50, current_y)
    current_y -= 200  # Adjust space for the next table

    # Transfer Details
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transfers.instructed_amount.amount} {transfers.instructed_amount.currency}"],
        ["Requested Execution Date", transfers.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transfers.purpose_code],
        ["Remittance Information (Structured)", transfers.remittance_information_structured or 'N/A'],
        ["Remittance Information (Unstructured)", transfers.remittance_information_unstructured or 'N/A'],
        ["Auth ID", transfers.auth_id],
        ["Transaction Status", transfers.get_transaction_status_display()],
        ["Priority", "High (Instant SEPA Credit Transfer)"]
    ]
    transfer_table = Table(transfer_data, colWidths=[200, 250])
    transfer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    transfer_table.wrapOn(c, 50, current_y)
    transfer_table.drawOn(c, 50, current_y)
    current_y -= 200  # Adjust space for the footer

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This document is an automatically generated receipt and does not require a signature.")

    # Save the PDF
    c.save()

    return pdf_path


import re
import uuid

# Constantes sensibles (idealmente cargar desde configuración o variables de entorno)


def validate_headers(headers):
    """
    Valida las cabeceras requeridas para las solicitudes SEPA.
    Retorna una lista de mensajes de error si alguna cabecera obligatoria falta 
    o no cumple el formato esperado.
    """
    errors = []
    idempotency_id = headers.get('idempotency-id', '')
    if not isinstance(idempotency_id, str):
        idempotency_id = str(idempotency_id)  # Normalizar a cadena
    if 'idempotency-id' not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', idempotency_id):
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
    if 'Origin' not in headers or not headers.get('Origin'):
        errors.append("Cabecera 'Origin' es requerida.")
    if 'x-request-id' not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', headers.get('x-request-id', '')):
        errors.append("Cabecera 'x-request-id' es requerida y debe ser un UUID válido.")
    return errors


def build_headers(request, external_method):
    """
    Construye un diccionario de cabeceras base para la llamada a la API SEPA, 
    tomando los valores de la solicitud Django (`request`). El parámetro 
    `external_method` indica el método HTTP que usará la API externa 
    (por ejemplo: 'POST', 'GET', 'PATCH', 'DELETE').
    """
    method = external_method.upper()
    headers = {}
    # Cabecera idempotency-id
    if method in ['POST', 'GET']:
        # Generar nuevo UUID si no se proporciona (p. ej. iniciar transferencia o consultar estado)
        headers['idempotency-id'] = request.headers.get('idempotency-id', str(uuid.uuid4()))
    else:
        # Requerir el idempotency-id proporcionado (p. ej. cancelación o segundo factor)
        headers['idempotency-id'] = request.headers.get('idempotency-id')
    # Cabecera OTP
    if method == 'POST':
        # En iniciar transferencia, usar OTP del formulario o valor por defecto para generar desafío
        headers['otp'] = request.POST.get('otp', 'SEPA_TRANSFER_GRANT')
    elif method in ['PATCH', 'DELETE']:
        # En cancelación o segundo factor, tomar OTP de los encabezados de la petición
        headers['otp'] = request.headers.get('otp')
    # (Para 'GET', la cabecera OTP no se incluye ya que no se requiere segundo factor en consulta de estado)
    # Cabecera Correlation-Id
    if method == 'POST':
        headers['Correlation-Id'] = request.headers.get('Correlation-Id', str(uuid.uuid4()))
    else:
        corr_id = request.headers.get('Correlation-Id')
        if corr_id:
            headers['Correlation-Id'] = corr_id
    # Cabecera apikey
    headers['apikey'] = request.headers.get('apikey')
    # Cabeceras opcionales process-id y previewsignature (solo en flujos con segundo factor)
    process_id = request.headers.get('process-id')
    if process_id:
        headers['process-id'] = process_id
    preview_sig = request.headers.get('previewsignature')
    if preview_sig:
        headers['previewsignature'] = preview_sig
    # Cabecera x-request-id (UUID único por solicitud)
    xreq = request.headers.get('x-request-id')
    if not xreq:
        xreq = str(uuid.uuid4())
    headers['x-request-id'] = xreq
    # Cabeceras de control de solicitud (CORS y contexto de petición)
    headers['Origin'] = ORIGIN
    headers['X-Requested-With'] = 'XMLHttpRequest'
    return headers

def attach_common_headers(headers, external_method):
    """
    Agrega cabeceras comunes a la petición API, como autenticación y tipo de contenido,
    según el método HTTP externo especificado.
    """
    # Autenticación con token Bearer
    headers['Authorization'] = f"Bearer {ACCESS_TOKEN}"
    # Aceptación de respuesta JSON en todos los casos
    headers['Accept'] = 'application/json'
    # En métodos con cuerpo (POST/PATCH), especificar el tipo de contenido JSON
    if external_method.upper() in ['POST', 'PATCH']:
        headers['Content-Type'] = 'application/json'
    return headers


def validate_parameters(data):
    """Valida los parámetros requeridos en el cuerpo de la solicitud."""
    errors = []
    if 'iban' in data and not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', data['iban']):
        errors.append("El IBAN proporcionado no es válido.")
        
    if 'requestedExecutionDate' in data:
        try:
            datetime.strptime(data['requestedExecutionDate'], '%Y-%m-%d')
        except ValueError:
            errors.append("El formato de 'requestedExecutionDate' debe ser yyyy-MM-dd.")
            
    if 'createDateTime' in data:
        try:
            datetime.strptime(data['createDateTime'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            errors.append("El formato de 'createDateTime' debe ser yyyy-MM-dd'T'HH:mm:ss.")
            
    if 'currency' in data and not re.match(r'^[A-Z]{3}$', data['currency']):
        errors.append("La moneda debe ser un código ISO 4217 válido (ejemplo: EUR).")
        
    if 'amount' in data and (not isinstance(data['amount'], (int, float)) or data['amount'] <= 0):
        errors.append("El monto debe ser un número positivo.")
        
    if 'transactionStatus' in data and data['transactionStatus'] not in ['RJCT', 'RCVD', 'ACCP', 'ACTC', 'ACSP', 'ACSC', 'ACWC', 'ACWP', 'ACCC', 'CANC', 'PDNG']:
        errors.append("El estado de la transacción no es válido.")
        
    if 'action' in data and data['action'] not in ['CREATE', 'CANCEL']:
        errors.append("El valor de 'action' no es válido. Valores permitidos: 'CREATE', 'CANCEL'.")
        
    if 'chargeBearer' in data and len(data['chargeBearer']) > 35:
        errors.append("El valor de 'chargeBearer' no debe exceder los 35 caracteres.")
        
    return errors