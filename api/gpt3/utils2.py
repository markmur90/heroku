import os
import re
import json
import uuid
import logging
import qrcode
import requests
from datetime import datetime
from requests.structures import CaseInsensitiveDict
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from jsonschema import validate as json_validate, ValidationError
from requests_oauthlib import OAuth2Session
from api.gpt3.helpers import obtener_ruta_schema_transferencia
from api.gpt3.models import SepaCreditTransfer
from api.gpt3.schemas import sepa_credit_transfer_schema
from config import settings

logger = logging.getLogger(__name__)

# Configuraciones iniciales
ORIGIN = settings.ORIGIN
CLIENT_ID = settings.CLIENT_ID
# ACCESS_TOKEN = settings.ACCESS_TOKEN

TIMEOUT_REQUEST = 10

# Directorio de logs
LOGS_DIR = os.path.join("schemas", "transferencias")
os.makedirs(LOGS_DIR, exist_ok=True)
SCHEMA_DIR = os.path.join("schemas", "transferencias")
os.makedirs(SCHEMA_DIR, exist_ok=True)

# Headers genéricos base
HEADERS_DEFAULT = {
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

def validate_headers(headers):
    errors = []
    if "idempotency-id" not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', str(headers.get('idempotency-id', ''))):
        errors.append("Cabecera 'idempotency-id' es obligatoria y debe ser UUID.")
    if "otp" in headers and not headers["otp"]:
        errors.append("Cabecera 'otp' no puede estar vacía si se envía.")
    if "Correlation-Id" in headers and len(headers["Correlation-Id"]) > 50:
        errors.append("Cabecera 'Correlation-Id' debe ser máximo 50 caracteres.")
    if "Origin" not in headers or not headers.get("Origin"):
        errors.append("Cabecera 'Origin' es obligatoria.")
    if "x-request-id" not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', str(headers.get('x-request-id', ''))):
        errors.append("Cabecera 'x-request-id' debe ser UUID válido.")
    return errors


def build_complete_sepa_headers(request, method: str) -> CaseInsensitiveDict:
    method = method.upper()
    headers = CaseInsensitiveDict()
    headers["idempotency-id"] = request.headers.get("idempotency-id", str(uuid.uuid4()))
    headers["x-request-id"] = request.headers.get("x-request-id", str(uuid.uuid4()))
    headers["Correlation-Id"] = request.headers.get("Correlation-Id", str(uuid.uuid4()))
    headers["Origin"] = request.headers.get("Origin", ORIGIN)
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Accept"] = "application/json"
    # headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
    if method in ['POST', 'PATCH', 'DELETE']:
        headers["Content-Type"] = "application/json"
        headers["otp"] = request.POST.get("otp") or request.headers.get("otp", "SEPA_TRANSFER_GRANT")
    process_id = request.headers.get('process-id')
    if process_id:
        headers['process-id'] = process_id
    preview_sig = request.headers.get('previewsignature')
    if preview_sig:
        headers['previewsignature'] = preview_sig
    errors = validate_headers(headers)
    if errors:
        raise ValueError(f"Errores en headers: {', '.join(errors)}")
    return headers


def validate_schema(data, schema):
    try:
        json_validate(instance=data, schema=schema)
        return {"success": True}
    except ValidationError as e:
        return {"success": False, "error": str(e)}


def obtener_ruta_schema_transferencia(payment_id):
    carpeta = os.path.join(SCHEMA_DIR, str(payment_id))
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def generar_otp_sepa_transfer():
    url = "https://api.db.com/gw/dbapi/others/onetimepasswords/v2/single"
    payload = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "language": "es"
    }
    headers = HEADERS_DEFAULT.copy()
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT_REQUEST)
        if resp.status_code != 200:
            err = handle_error_response(resp)
            registrar_log("", headers, resp.text, err)
            return {"success": False, "error": err}
        data = resp.json()
        token = data.get("challengeProofToken")
        if not token:
            raise Exception("OTP no recibido.")
        registrar_log("", headers, resp.text, None)
        return {"success": True, "otp": token}
    except Exception as e:
        registrar_log("", headers, "", str(e))
        return {"success": False, "error": str(e)}
    
# def get_oauth_session(request=None):
#     try:
#         if not ACCESS_TOKEN:
#             raise ValueError("ACCESS_TOKEN no configurado.")
#         return OAuth2Session(client_id=CLIENT_ID, token={"access_token": ACCESS_TOKEN})
#     except Exception as e:
#         registrar_log("", {}, "", str(e))
#         raise

def guardar_pain002_si_aplica(response, payment_id):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    if "xml" in response.headers.get("Content-Type", ""):
        path = os.path.join(carpeta, f"pain002_{payment_id}.xml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(response.text)
            

def handle_error_response(response):
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
    return error_messages.get(response.status_code, response.text)

def preparar_payload_transferencia(transferencia, request=None):
    payload = {
        "creditor": {
            "creditorName": {"name": transferencia.creditor_name},
            "creditorPostalAddress": {
                "country": transferencia.creditor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.creditor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.creditor.postal_address.zip_code_and_city
                }
            }
        },
        "creditorAccount": {
            "iban": transferencia.creditor_account.iban,
            "currency": transferencia.creditor_account.currency
        },
        "creditorAgent": {
            "financialInstitutionId": transferencia.creditor_agent.financial_institution_id
        },
        "debtor": {
            "debtorName": {"name": transferencia.debtor_name},
            "debtorPostalAddress": {
                "country": transferencia.debtor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.debtor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.debtor.postal_address.zip_code_and_city
                }
            }
        },
        "debtorAccount": {
            "iban": transferencia.debtor_account.iban,
            "currency": transferencia.debtor_account.currency
        },
        "instructedAmount": {
            "amount": float(transferencia.amount),
            "currency": transferencia.currency
        },
        "paymentIdentification": {
            "endToEndIdentification": transferencia.payment_identification.end_to_end_id,
            "instructionId": transferencia.payment_identification.instruction_id
        },
        "purposeCode": transferencia.purpose_code,
        "requestedExecutionDate": transferencia.requested_date.strftime("%Y-%m-%d"),
        "remittanceInformationStructured": transferencia.remittance_information_structured,
        "remittanceInformationUnstructured": transferencia.remittance_information_unstructured
    }
    result = validate_schema(payload, sepa_credit_transfer_schema)
    if not result["success"]:
        raise ValueError(f"Error de validación JSON: {result['error']}")
    return payload


def construir_payload(transferencia: SepaCreditTransfer) -> dict:
    """
    Construye el payload para una transferencia SEPA usando objetos Django.
    """
    payload = preparar_payload_transferencia(transferencia)
    return payload

def registrar_log(payment_id, headers, response_text="", error=None):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    log_path = os.path.join(carpeta, f"transferencia_{payment_id}.log")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write("\n" + "=" * 40 + "\n")
        log.write(f"Fecha y hora: {datetime.now()}\n")
        log.write("=== Headers ===\n")
        log.write(json.dumps(headers, indent=2))
        log.write("\n")
        if error:
            log.write("=== Error ===\n")
            log.write(str(error) + "\n")
        else:
            log.write("=== Response ===\n")
            log.write(response_text + "\n")



# Guardar pain.002 si el banco responde en XML
def guardar_pain002_si_aplica(response, payment_id):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    content_type = response.headers.get("Content-Type", "")
    if "xml" in content_type and response.text:
        xml_response_path = os.path.join(carpeta, f"pain002_{payment_id}.xml")
        with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(response.text)