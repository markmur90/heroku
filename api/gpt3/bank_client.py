import json
import uuid
import requests
import logging
import os
import xml.etree.ElementTree as ET
from cryptography.fernet import Fernet
from lxml import etree

from config import settings

from .utils2 import (
    HEADERS_DEFAULT,
    TIMEOUT_REQUEST,
    build_complete_sepa_headers,
    obtener_ruta_schema_transferencia,
    registrar_log,
    handle_error_response
)

# Logger para toda esta utilidad
logger = logging.getLogger(__name__)

# Configuraciones
TIMEOUT = (5, 5)  # (connect_timeout, read_timeout)
RETRY_COUNT = 3
RETRY_DELAY = 2

LOGS_DIR = os.path.join("schemas", "transferencias")
SCHEMA_DIR = os.path.join("schemas", "transferencias")

KEY_FILE =os.path.join(SCHEMA_DIR, 'secret.key')
SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'pain.002.001.03.xsd')
SCHEMA_PATH_PAIN001 = os.path.join(SCHEMA_DIR, 'pain.001.001.03.xsd')

# Asegurar que existan los directorios
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

URL = settings.API_URL

def _load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

encryptor = _load_key()



# Función para obtener clave de cifrado de logs (o crearla)
def get_encryption_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
    return Fernet(key)

encryptor = get_encryption_key()


# Función para ocultar OTP en logs
def mask_otp(otp):
    if len(otp) <= 4:
        return '**' + otp[-2:]
    return otp[:2] + '**' + otp[-2:]




# Función para validar un XML contra el esquema pain.002
def validate_pain002(xml_text, payment_id):
    try:
        xml_doc = etree.fromstring(xml_text.encode("utf-8"))
        schema_file = os.path.join("schemas", "transferencias", "pain.002.001.03.xsd")
        with open(schema_file, "rb") as f:
            schema_doc = etree.parse(f)
            schema = etree.XMLSchema(schema_doc)
        schema.assertValid(xml_doc)
        registrar_log(payment_id, {}, xml_text, None)
        return {"success": True}
    except Exception as e:
        registrar_log(payment_id, {}, xml_text, str(e))
        return {"success": False, "error": str(e)}


# Función para validar XML pain.001 contra el XSD oficial
def validate_pain001(xml_text):
    try:
        xml_doc = etree.fromstring(xml_text.encode("utf-8"))
        schema_file = os.path.join("schemas", "transferencias", "pain.001.001.03.xsd")
        with open(schema_file, "rb") as f:
            schema_doc = etree.parse(f)
            schema = etree.XMLSchema(schema_doc)
        schema.assertValid(xml_doc)
        registrar_log("", {}, xml_text, None)
        return {"success": True}
    except Exception as e:
        registrar_log("", {}, xml_text, str(e))
        return {"success": False, "error": str(e)}


# Función principal para enviar una transferencia SEPA
def send_sepa_transfer(payment_id, payload, otp, access_token):
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {access_token}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
        
        'otp': otp,
    })
    try:
        resp = requests.post(URL, json=payload, headers=headers, timeout=(5,15))
        registrar_log(payment_id, headers, resp.text, None)
        if resp.status_code not in (200, 201):
            err = handle_error_response(resp)
            registrar_log(payment_id, headers, resp.text, err)
            return {"success": False, "error": err}
        return {"success": True, "response": resp.json()}
    except Exception as e:
        registrar_log(payment_id, headers, "", str(e))
        return {"success": False, "error": str(e)}


# Función para obtener el estado de una transferencia SEPA
def get_sepa_transfer_status(payment_id, access_token):
    url = f"{URL}/{payment_id}/status"
    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {access_token}",
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
        })
    try:
        resp = requests.get(url, headers=headers, timeout=(5,15))
        registrar_log(payment_id, headers, resp.text, None)
        if resp.status_code not in (200, 201):
            err = handle_error_response(resp)
            registrar_log(payment_id, headers, resp.text, err)
            return {"success": False, "error": err}
        data = resp.json()
        status = data.get("transactionStatus")
        return {"success": True, "status": status}
    except Exception as e:
        registrar_log(payment_id, headers, "", str(e))
        return {"success": False, "error": str(e)}




# Función para cancelar una transferencia SEPA
def cancel_sepa_transfer(payment_id, otp, access_token):
    url = f'{URL}/{payment_id}'
    headers = build_complete_sepa_headers({
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': str(payment_id),
        'otp': otp,
    }, 'DELETE')  # Construir headers usando build_complete_sepa_headers
    return _delete_request(url, payment_id, otp, access_token)


# Función para reintentar second factor authentication
def retry_second_factor(payment_id, payload, otp, access_token):
    url = f'{URL}/{payment_id}'
    headers = build_complete_sepa_headers({
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': str(payment_id),
        'otp': otp,
    }, 'PATCH')  # Construir headers usando build_complete_sepa_headers
    return _patch_request(url, payment_id, payload, otp, access_token)


# Funciones internas genericas

def _post_request(url, payment_id, payload, headers):
    # Llama a _send_request con el método POST
    return _send_request('POST', url, headers, payload, payment_id)


def _get_request(url, payment_id, access_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    # Llama a _send_request con el método GET
    return _send_request('GET', url, headers, None, payment_id)


def _delete_request(url, payment_id, otp, access_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': str(payment_id),
        'otp': otp,
    }
    # Llama a _send_request con el método DELETE
    return _send_request('DELETE', url, headers, None, payment_id)


def _patch_request(url, payment_id, payload, otp, access_token):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': str(payment_id),
        'otp': otp,
    }
    # Llama a _send_request con el método PATCH
    return _send_request('PATCH', url, headers, payload, payment_id)


def _send_request(method, url, headers, payload, payment_id):
    session = requests.Session()
    attempt = 0
    while attempt < RETRY_COUNT:
        try:
            # Selecciona el método HTTP adecuado
            if method == 'POST':
                response = session.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            elif method == 'GET':
                response = session.get(url, headers=headers, timeout=TIMEOUT)
            elif method == 'DELETE':
                response = session.delete(url, headers=headers, timeout=TIMEOUT)
            elif method == 'PATCH':
                response = session.patch(url, json=payload, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError("Método HTTP no soportado.")

            # Guarda los logs de la solicitud y la respuesta
            request_info = f"Request Headers: {headers}\nPayload: {payload}"
            response_info = f"Response Status: {response.status_code}\nResponse Headers: {dict(response.headers)}\nResponse Body: {response.text}"
            registrar_log(payment_id, headers, response.text)

            # Valida el XML si el contenido es de tipo XML
            if 'xml' in response.headers.get('Content-Type', ''):
                validate_pain002(response.text)

            # Verifica si la respuesta tiene errores
            if response.status_code not in [200, 201]:
                mensaje = handle_error_response(response)
                registrar_log(payment_id, headers, response.text, error=mensaje)
                return {"error": mensaje}

            return response  # Devuelve el objeto response completo
        except requests.RequestException as e:
            # Manejo de errores y reintentos
            carpeta_transferencia = os.path.join(LOGS_DIR, str(payment_id))
            os.makedirs(carpeta_transferencia, exist_ok=True)
            error_log_path = os.path.join(carpeta_transferencia, f"error_{payment_id}.log")
            with open(error_log_path, 'a', encoding='utf-8') as error_file:
                error_file.write(f"Intento {attempt + 1} fallido: {str(e)}\n")
            registrar_log(payment_id, headers, "", error=str(e))
            logging.error(f"Intento {attempt + 1} fallido: {e}")
            attempt += 1
            if attempt >= RETRY_COUNT:
                return {"error": "No se pudo completar la operación tras varios intentos."}


