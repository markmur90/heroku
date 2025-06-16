import logging
import uuid
from requests_oauthlib import OAuth2Session
from django.conf import settings
logger = logging.getLogger(__name__)

# Token de acceso dummy (debería obtenerse con autenticación OAuth real)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'

CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'


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
        ["Idempotency Key", transfers.idempotency_key]
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