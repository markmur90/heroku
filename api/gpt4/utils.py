# /home/markmur88/api_bank_h2/api/gpt4/utils.py
import os
import time
import uuid
import json
import logging
import random
import string
import hashlib
import base64
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from django.shortcuts import get_object_or_404
from jsonschema import validate
from lxml import etree
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
import jwt
from cryptography.hazmat.primitives import serialization

from api.gpt4.models import LogTransferencia, Transfer



# ==== Directorios de schemas y logs ====
BASE_SCHEMA_DIR = os.path.join("schemas", "transferencias")
os.makedirs(BASE_SCHEMA_DIR, exist_ok=True)
TRANSFER_LOG_DIR = BASE_SCHEMA_DIR  # logs por transferencia
GLOBAL_LOG_FILE = os.path.join(TRANSFER_LOG_DIR, 'global_errors.log')


BASE_DIR = Path(__file__).resolve().parent.parent.parent

def get_project_path(*rel_path: str | Path) -> str:
    return str(BASE_DIR.joinpath(*rel_path))

# ==== Configuración general ====
from functools import lru_cache
from api.configuraciones_api.helpers import get_conf

@lru_cache
def get_settings():
    timeout = int(600)
    return {
        "ORIGIN":        get_conf("ORIGIN"),
        "CLIENT_ID":     get_conf("CLIENT_ID"),
        "CLIENT_SECRET": get_conf("CLIENT_SECRET"),
        "TOKEN_URL":     get_conf("TOKEN_URL"),
        "AUTH_URL":      get_conf("AUTH_URL"),
        "API_URL":       get_conf("API_URL"),
        "TIMEOUT_REQUEST": timeout,
        "REDIRECT_URI":  get_conf("REDIRECT_URI"),
        "SCOPE":         get_conf("SCOPE"),
        "AUTHORIZE_URL": get_conf("AUTHORIZE_URL"),
        "OAUTH2": {
            "CLIENT_ID":     get_conf("CLIENT_ID"),
            "CLIENT_SECRET": get_conf("CLIENT_SECRET"),
            "TOKEN_URL":     get_conf("TOKEN_URL"),
            "REDIRECT_URI":  get_conf("REDIRECT_URI"),
            "SCOPE":         get_conf("SCOPE"),
            "AUTHORIZE_URL": get_conf("AUTHORIZE_URL"),
            "TIMEOUT_REQUEST": timeout,
        },
    }


# Ejemplo de uso:
# settings = get_settings()
# token_url = settings["TOKEN_URL"]

logger = logging.getLogger(__name__)


# ===========================
# GENERADORES DE ID
# ===========================
def generate_unique_code(length=35) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_message_id(prefix='MSG'):
    return f"{prefix}-{generate_unique_code(20)}"

def generate_instruction_id():
    return generate_unique_code(20)

def generate_end_to_end_id():
    return generate_unique_code(30)

def generate_correlation_id():
    return generate_unique_code(30)

def generate_deterministic_id(*args, prefix="") -> str:
    raw = ''.join(str(a) for a in args)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return (prefix + h)[:35]

def generate_payment_id_uuid() -> str:
    return uuid.uuid4()



def obtener_ruta_schema_transferencia(payment_id: str) -> str:
    carpeta = os.path.join(BASE_SCHEMA_DIR, str(payment_id))
    os.makedirs(carpeta, exist_ok=True)
    return carpeta

def registrar_log_oauth(accion, estado, metadata=None, error=None, request=None):
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'accion': accion,
        'estado': estado,
        'metadata': metadata or {},
        'error': error
    }
    entry = json.dumps(log_entry, indent=2)

    log_dir = os.path.join(BASE_SCHEMA_DIR, "OAUTH_LOGS")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "oauth_general.log")

    session_id = None
    if request and hasattr(request, 'session'):
        session_id = request.session.session_key

    session_log_file = os.path.join(log_dir, f"oauth_general.log") if session_id else None

    try:
        with open(log_file, 'a') as f:
            f.write(entry + "\n")
        if session_log_file:
            with open(session_log_file, 'a') as f:
                f.write(entry + "\n")
    except Exception as e:
        print(f"Error escribiendo logs OAuth: {str(e)}")

    registro = request.session.get('current_payment_id') if request and hasattr(request, 'session') else None
    if not registro:
        registro = session_id or "SIN_SESION"

    try:
        LogTransferencia.objects.create(
            registro=registro,
            tipo_log='AUTH',
            contenido=entry
        )
    except Exception as e:
        with open(GLOBAL_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] Error guardando log OAuth en DB: {str(e)}\n")

    registrar_log(
        registro=registro,
        tipo_log='AUTH',
        request_body=metadata,
        error=error,
        extra_info=f"OAuth: {accion} - {estado}"
    )


def registrar_log(
    registro: str,
    tipo_log: str = 'TRANSFER',
    headers_enviados: dict = None,
    request_body: any = None,
    response_headers: dict = None,
    response_text: str = None,
    error: any = None,
    extra_info: str = None
):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = "\n" + "=" * 80 + "\n"
    entry += f"Fecha y hora: {timestamp}\n" + "=" * 80 + "\n"

    if extra_info:
        entry += f"=== Info ===\n{extra_info}\n\n"
    if headers_enviados:
        try:
            entry += "=== Headers enviados ===\n" + json.dumps(headers_enviados, indent=4) + "\n\n"
        except Exception:
            entry += "=== Headers enviados (sin formato) ===\n" + str(headers_enviados) + "\n\n"
    if request_body:
        try:
            entry += "=== Body de la petición ===\n" + json.dumps(request_body, indent=4, default=str) + "\n\n"
        except Exception:
            entry += "=== Body de la petición (sin formato) ===\n" + str(request_body) + "\n\n"
    if response_headers:
        try:
            entry += "=== Response Headers ===\n" + json.dumps(response_headers, indent=4) + "\n\n"
        except Exception:
            entry += "=== Response Headers (sin formato) ===\n" + str(response_headers) + "\n\n"
    if response_text:
        entry += "=== Respuesta ===\n" + str(response_text) + "\n\n"
    if error:
        entry += "=== Error ===\n" + str(error) + "\n"

    carpeta = obtener_ruta_schema_transferencia(registro)
    log_path = os.path.join(carpeta, f"transferencia_{registro}.log")
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        with open(GLOBAL_LOG_FILE, 'a', encoding='utf-8') as gf:
            gf.write(f"[{timestamp}] ERROR AL GUARDAR EN ARCHIVO {registro}.log: {str(e)}\n")

    try:
        LogTransferencia.objects.create(
            registro=registro,
            tipo_log=tipo_log or 'ERROR',
            contenido=entry
        )
    except Exception as e:
        with open(GLOBAL_LOG_FILE, 'a', encoding='utf-8') as gf:
            gf.write(f"[{timestamp}] ERROR AL GUARDAR LOG EN DB para {registro}: {str(e)}\n")

    if error:
        with open(GLOBAL_LOG_FILE, 'a', encoding='utf-8') as gf:
            gf.write(f"[{timestamp}] ERROR [{registro}]: {str(error)}\n")
            
     
     
# ===========================
# XML Y AML
# ===========================
def generar_xml_pain001(transferencia: Transfer, payment_id: str) -> str:
    ruta = obtener_ruta_schema_transferencia(payment_id)
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    
    cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")
    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    ET.SubElement(grp_hdr, "CtrlSum").text = str(transferencia.instructed_amount)
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = transferencia.debtor.name
    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "BtchBookg").text = "false"
    ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
    ET.SubElement(pmt_inf, "CtrlSum").text = str(transferencia.instructed_amount)
    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = "SEPA"
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = transferencia.debtor.name
    dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
    ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transferencia.debtor.postal_address_street
    ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transferencia.debtor.postal_address_city
    ET.SubElement(dbtr_pstl_adr, "Ctry").text = transferencia.debtor.postal_address_country
    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
    ET.SubElement(dbtr_acct_id, "IBAN").text = transferencia.debtor_account.iban
    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = str(transferencia.payment_identification.end_to_end_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_id, "InstrId").text = str(transferencia.payment_identification.instruction_id)
    amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
    ET.SubElement(amt, "InstdAmt", Ccy=transferencia.currency).text = str(transferencia.instructed_amount)
    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = transferencia.creditor.name
    cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
    ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transferencia.creditor.postal_address_street
    ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transferencia.creditor.postal_address_city
    ET.SubElement(cdtr_pstl_adr, "Ctry").text = transferencia.creditor.postal_address_country
    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
    ET.SubElement(cdtr_acct_id, "IBAN").text = transferencia.creditor_account.iban
    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(fin_instn_id, "BIC").text = transferencia.creditor_agent.bic
    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    if transferencia.remittance_information_unstructured:
        ET.SubElement(rmt_inf, "Ustrd").text = transferencia.remittance_information_unstructured or ""
        
    xml_path = os.path.join(ruta, f"pain001_{payment_id}.xml")
    ET.ElementTree(root).write(xml_path, encoding='utf-8', xml_declaration=True)
    registrar_log(payment_id, tipo_log='XML', extra_info=f"XML pain.001 generado en {xml_path}")
    return xml_path

def generar_xml_pain002(data, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.002.001.03")
    rpt = ET.SubElement(root, "CstmrPmtStsRpt")
    grp_hdr = ET.SubElement(rpt, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = str(payment_id)
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    orgnl_grp_inf = ET.SubElement(rpt, "OrgnlGrpInfAndSts")
    ET.SubElement(orgnl_grp_inf, "OrgnlMsgId").text = str(payment_id)
    ET.SubElement(orgnl_grp_inf, "OrgnlMsgNmId").text = "pain.001.001.03"
    ET.SubElement(orgnl_grp_inf, "OrgnlNbOfTxs").text = "1"
    ET.SubElement(orgnl_grp_inf, "OrgnlCtrlSum").text = str(data["instructedAmount"]["amount"])
    ET.SubElement(orgnl_grp_inf, "GrpSts").text = data["transactionStatus"]
    tx_inf = ET.SubElement(rpt, "TxInfAndSts")
    ET.SubElement(tx_inf, "OrgnlInstrId").text = data["paymentIdentification"]["instructionId"]
    ET.SubElement(tx_inf, "OrgnlEndToEndId").text = data["paymentIdentification"]["endToEndId"]
    ET.SubElement(tx_inf, "TxSts").text = data["transactionStatus"]
    
    xml_filename = f"pain002_{payment_id}.xml"
    xml_path = os.path.join(carpeta_transferencia, xml_filename)
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    validar_xml_con_xsd(xml_path, xsd_path="schemas/xsd/pain.002.001.03")
    return xml_path

def validar_xml_pain001(xml_path: str):
    tree = ET.parse(xml_path)
    ns = {'ns': "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}
    if tree.find('.//ns:EndToEndId', ns) is None:
        raise ValueError("El XML no contiene un EndToEndId válido.")


def validar_xml_con_xsd(xml_path, xsd_path="schemas/xsd/pain.001.001.03.xsd"):
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
    with open(xml_path, 'rb') as f:
        xml_doc = etree.parse(f)
    if not schema.validate(xml_doc):
        errors = schema.error_log
        raise ValueError(f"El XML no es válido según el XSD: {errors}")
    
    
def validar_aml_con_xsd(aml_path: str, xsd_path="schemas/xsd/aml_transaction_report.xsd"):
    schema_root = etree.parse(xsd_path)
    schema = etree.XMLSchema(schema_root)
    xml_doc = etree.parse(aml_path)
    if not schema.validate(xml_doc):
        raise ValueError(f"AML inválido según XSD: {schema.error_log}")

    
def generar_archivo_aml(transferencia: Transfer, payment_id: str) -> str:
    ruta = obtener_ruta_schema_transferencia(payment_id)
    aml_filename = f"aml_{payment_id}.xml"
    aml_path = os.path.join(ruta, f"aml_{payment_id}.xml")
    
    root = ET.Element("AMLTransactionReport")
    transaction = ET.SubElement(root, "Transaction")
    ET.SubElement(transaction, "TransactionID").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(transaction, "TransactionType").text = "SEPA" # type: ignore
    ET.SubElement(transaction, "ExecutionDate").text = transferencia.requested_execution_date.strftime("%Y-%m-%dT%H:%M:%S")
    amount = ET.SubElement(transaction, "Amount")
    amount.set("currency", transferencia.currency)
    amount.text = str(transferencia.instructed_amount)
    debtor = ET.SubElement(transaction, "Debtor")
    ET.SubElement(debtor, "Name").text = transferencia.debtor.name
    ET.SubElement(debtor, "IBAN").text = transferencia.debtor_account.iban
    ET.SubElement(debtor, "Country").text = transferencia.debtor.postal_address_country
    ET.SubElement(debtor, "CustomerID").text = transferencia.debtor.customer_id
    ET.SubElement(debtor, "KYCVerified").text = "true"
    creditor = ET.SubElement(transaction, "Creditor")
    ET.SubElement(creditor, "Name").text = transferencia.creditor.name
    ET.SubElement(creditor, "IBAN").text = transferencia.creditor_account.iban
    ET.SubElement(creditor, "BIC").text = transferencia.creditor_agent.financial_institution_id
    ET.SubElement(creditor, "Country").text = transferencia.creditor.postal_address_country
    ET.SubElement(transaction, "Purpose").text = transferencia.purpose_code or "N/A"
    ET.SubElement(transaction, "Channel").text = "Online"
    ET.SubElement(transaction, "RiskScore").text = "3"
    ET.SubElement(transaction, "PEP").text = "false"
    ET.SubElement(transaction, "SanctionsCheck").text = "clear"
    ET.SubElement(transaction, "HighRiskCountry").text = "false"
    flags = ET.SubElement(transaction, "Flags")
    ET.SubElement(flags, "UnusualAmount").text = "false"
    ET.SubElement(flags, "FrequentTransfers").text = "false"
    ET.SubElement(flags, "ManualReviewRequired").text = "false"
    ET.ElementTree(root).write(aml_path, encoding="utf-8", xml_declaration=True)
    
    registrar_log(payment_id, tipo_log='AML', extra_info=f"Archivo AML generado en {aml_path}")
    return aml_path


# ===========================
# LOGS Y HEADERS
# ===========================
def setup_logger(payment_id):
    logger = logging.getLogger(f'transferencia_{payment_id}')
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(TRANSFER_LOG_DIR, f'transferencia_{payment_id}.log'))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger



def read_log_file(payment_id):
    log_path = os.path.join(TRANSFER_LOG_DIR, f'transferencia_{payment_id}.log')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def handle_error_response(response):
    if isinstance(response, Exception):
        return str(response)
    errores = {
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
    try:
        data = response.json()
    except ValueError:
        return response.text if hasattr(response, 'text') else str(response)
    code = data.get('code') or data.get('errorCode') if isinstance(data, dict) else None
    try:
        code_int = int(code) if code is not None else None
        if code_int in errores:
            return errores[code_int]
    except (ValueError, TypeError):
        pass
    if isinstance(data, dict) and 'message' in data:
        return data['message']
    if isinstance(data, list):
        return "; ".join(item.get('message', str(item)) for item in data)
    return response.text if hasattr(response, 'text') else str(response)


def default_request_headers():
    settings = get_settings()
    ORIGIN = settings["ORIGIN"]
    return {
        "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
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
        "Strict-Transport-Security": "max-age=3153TIMEOUT_REQUEST0; includeSubDomains; preload",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        'x-request-Id': str(Transfer.payment_id),
        "X-Requested-With": "XMLHttpRequest", 
    }

# ===========================
# 6. Creación de PDFs de Transferencia
# ===========================
def generar_pdf_transferencia(transferencia: Transfer) -> str:
    creditor_name = transferencia.creditor.name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transferencia.payment_id
    ruta = obtener_ruta_schema_transferencia(transferencia.payment_id)
        
    pdf_filename = f"{creditor_name}_{timestamp}_{payment_reference}.pdf"
    pdf_path = os.path.join(ruta, f"{transferencia.payment_id}.pdf")
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    current_y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, current_y, "SEPA Transfer Receipt")
    current_y = 650
    header_data = [
        ["Creation Date", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
        ["Payment Reference", transferencia.payment_id]
    ]
    crear_tabla_pdf(c, header_data, current_y)
    current_y -= 120
    debtor_data = [
        ["Debtor Information", ""],
        ["Name", transferencia.debtor.name],
        ["IBAN", transferencia.debtor_account.iban],
        # ["Customer ID", transferencia.debtor.customer_id],
        ["Address", f"{transferencia.debtor.postal_address_country}, {transferencia.debtor.postal_address_city}, {transferencia.debtor.postal_address_street}"]
    ]
    crear_tabla_pdf(c, debtor_data, current_y)
    current_y -= 120
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transferencia.creditor.name],
        ["IBAN", transferencia.creditor_account.iban],
        ["BIC", transferencia.creditor_agent.bic],
        ["Address", f"{transferencia.creditor.postal_address_country}, {transferencia.creditor.postal_address_city}, {transferencia.creditor.postal_address_street}"]
    ]
    crear_tabla_pdf(c, creditor_data, current_y)
    current_y -= 200
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transferencia.instructed_amount} {transferencia.currency}"],
        ["Requested Execution Date", transferencia.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transferencia.purpose_code],
        ["Remittance Info Unstructured", transferencia.remittance_information_unstructured or ""],
        ["Transaction Status", transferencia.status],
    ]
    crear_tabla_pdf(c, transfer_data, current_y)
    c.showPage()
    qr = qrcode.make(transferencia.payment_id)
    qr_path = os.path.join(ruta, f"qr_{transferencia.payment_id}.png")
    qr.save(qr_path)
    qr_image = ImageReader(qr_path)
    c.drawImage(qr_image, width / 2.0 - 75, height / 2.0 - 75, width=150, height=150)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, 50, "Generated automatically by SEPA Transfer System.")
    c.save()
    if os.path.exists(qr_path):
        os.remove(qr_path)
    registrar_log(transferencia.payment_id, tipo_log='TRANSFER', extra_info=f"PDF generado en {pdf_path}")
    return pdf_path

def crear_tabla_pdf(c, data, y_position):
    table = Table(data, colWidths=[180, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    table.wrapOn(c, 50, y_position)
    table.drawOn(c, 50, y_position)



# ===========================
# SEND TRANSFER
# ===========================
def send_transfer0(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    settings = get_settings()
    API_URL = settings["API_URL"]    
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    schema_data = transfer.to_schema_data()
    token = use_token if use_token and not regenerate_token else get_access_token(transfer.payment_id)
    proof_token, token = (use_otp, token) if use_otp and not regenerate_otp else obtener_otp_automatico_con_challenge(transfer)

    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': transfer.payment_id,
        'Correlation-Id': transfer.payment_id,
        'Otp': proof_token
    })
    try:
        response = requests.post(API_URL, headers=headers, json=schema_data, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        data = response.json()
        transfer.auth_id = data.get('authId')
        transfer.status = data.get('transactionStatus', transfer.status)
        transfer.save()
        registrar_log(
            transfer.payment_id,
            request_headers=headers,
            request_body=schema_data,
            response_headers=dict(response.headers),
            response_body=response.text,
            tipo_log='TRANSFER'
        )
    except requests.RequestException as e:
        error_msg = handle_error_response(e)
        registrar_log(
            transfer.payment_id,
            request_headers=headers,
            request_body=schema_data,
            error=error_msg,
            extra_info="Error de conexión enviando transferencia",
            tipo_log='ERROR'
        )
        raise
    try:
        xml_path = generar_xml_pain001(transfer, transfer.payment_id)
        aml_path = generar_archivo_aml(transfer, transfer.payment_id)
        validar_xml_pain001(xml_path)
        validar_xml_con_xsd(xml_path)
        validar_aml_con_xsd(aml_path)
        setup_logger(transfer.payment_id).info("Validación de XML y AML superada correctamente.")
    except Exception as e:
        registrar_log(
            transfer.payment_id,
            tipo_log='ERROR',
            response_body=f"Error generando XML o AML posterior: {str(e)}"
        )
    return response

def send_transfer1(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    settings = get_settings()
    API_URL = settings["API_URL"]    
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    proof_token, token = obtener_otp_automatico_con_challenge(transfer.payment_id) if regenerate_otp or not use_otp else (use_otp, token)
    token = get_access_token(transfer.payment_id) if regenerate_token or not use_token else use_token
    schema_data = transfer.to_schema_data()
    headers = default_request_headers()
    headers.update({
        "Authorization": f"Bearer {token}",
        "idempotency-id": transfer.payment_id,
        "Correlation-Id": transfer.payment_id,
        "otp": proof_token
    })
    response = requests.post(API_URL, json=schema_data, headers=headers, timeout=TIMEOUT_REQUEST)
    data = response.json()
    transfer.auth_id = data.get("authId")
    transfer.status = data.get("transactionStatus", transfer.status)
    transfer.save()
    registrar_log(
        transfer.payment_id,
        request_headers=headers,
        request_body=schema_data,
        response_headers=dict(response.headers),
        response_body=response.text,
        tipo_log='TRANSFER'
    )
    return response

def send_transfer2(
    transfer: Transfer,
    use_token: Optional[str] = None,
    use_otp: Optional[str] = None,
    regenerate_token: bool = False,
    regenerate_otp: bool = False
) -> requests.Response:

    settings = get_settings()
    API_URL = settings["API_URL"]    
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    schema_data = transfer.to_schema_data()
    if use_token and not regenerate_token:
        token = use_token
    else:
        token = get_access_token(transfer.payment_id)
    if use_otp and not regenerate_otp:
        proof_token = use_otp
    else:
        proof_token, token = obtener_otp_automatico_con_challenge(transfer)
    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Idempotency-Id': transfer.payment_id,
        'Correlation-Id': transfer.payment_id,
        'Otp': proof_token
    })
    try:
        response = requests.post(API_URL, headers=headers, json=schema_data, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
    except requests.RequestException as exc:
        error_msg = handle_error_response(exc)
        registrar_log(
            transfer.payment_id,
            request_headers=headers,
            request_body=schema_data,
            error=error_msg,
            extra_info='Error de conexión enviando transferencia',
            tipo_log='ERROR'
        )
        raise
    data = response.json()
    transfer.auth_id = data.get('authId')
    transfer.status = data.get('transactionStatus', transfer.status)
    transfer.save()
    registrar_log(
        transfer.payment_id,
        request_headers=headers,
        request_body=schema_data,
        response_headers=dict(response.headers),
        response_body=response.text,
        tipo_log='TRANSFER'
        
    )
    try:
        xml_path = generar_xml_pain001(transfer, transfer.payment_id)
        aml_path = generar_archivo_aml(transfer, transfer.payment_id)
        validar_xml_pain001(xml_path)
        validar_xml_con_xsd(xml_path)
        validar_aml_con_xsd(aml_path)
        setup_logger(transfer.payment_id).info('Validación de XML y AML completada correctamente.')
    except Exception as exc:
        registrar_log(
            transfer.payment_id,
            response_body=f'Error generando XML o AML posterior: {exc}',
            tipo_log='ERROR'
        )
    return response

def send_transfer(transfer: Transfer, use_token: str = None, use_otp: str = None,
                  regenerate_token: bool = False, regenerate_otp: bool = False) -> requests.Response:
    settings = get_settings()
    API_URL = settings["API_URL"]    
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    pid = transfer.payment_id
    # 1️⃣ Token
    token = use_token if use_token and not regenerate_token else get_access_token(pid)
    # 2️⃣ OTP
    if use_otp and not regenerate_otp:
        otp = use_otp
    else:
        otp, token = obtener_otp_automatico(transfer)
    # 3️⃣ Cuerpo y headers
    body = transfer.to_schema_data()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'Idempotency-Id': pid,
        'Correlation-Id': pid,
        'Otp': otp
    }
    registrar_log(pid, headers_enviados=headers, request_body=body, tipo_log='TRANSFER', extra_info="Enviando transferencia SEPA")
    try:
        resp = requests.post(API_URL, headers=headers, json=body, timeout=TIMEOUT_REQUEST)
        response_headers = dict(resp.headers)
        registrar_log(pid, tipo_log='TRANSFER', response_text=resp.text, headers_enviados=response_headers, extra_info="Respuesta del API SEPA")
        resp.raise_for_status()
    except requests.RequestException as e:
        err = str(e)
        registrar_log(pid, error=err, tipo_log='ERROR', extra_info="Error HTTP enviando transferencia")
        raise
    data = resp.json()
    transfer.auth_id = data.get('authId')
    transfer.status = data.get('transactionStatus', transfer.status)
    transfer.save()
    registrar_log(pid, tipo_log='TRANSFER', extra_info="Transferencia enviada con éxito")
    # 4️⃣ Validaciones adicionales
    try:
        xml_path = generar_xml_pain001(transfer, pid)
        aml_path = generar_archivo_aml(transfer, pid)
        validar_xml_pain001(xml_path)
        validar_aml_con_xsd(aml_path)
        registrar_log(pid, tipo_log='TRANSFER' ,extra_info="Validación XML/AML completada")
    except Exception as e:
        registrar_log(pid, error=str(e), tipo_log='ERROR', extra_info="Error generando XML/AML posterior")
    return resp




def limpiar_datos_sensibles(data):
    """
    Limpia datos sensibles para logs sin truncar información importante
    """
    if isinstance(data, dict):
        cleaned = data.copy()
        for key in ['access_token', 'refresh_token', 'code_verifier']:
            if key in cleaned:
                cleaned[key] = "***REDACTED***"
        return cleaned
    return data



import requests
import hmac
import hashlib
from urllib.parse import urlencode
from datetime import timedelta

from django.utils.timezone import now
from django.utils.encoding import force_bytes

from api.gpt4.utils import registrar_log
from api.configuraciones_api.models import ConfiguracionAPI

# Cache in-memory per-process. For multi‐process deployments, replace with Django cache.
_access_token_cache = {}


def get_access_token(payment_id: str = None, force_refresh: bool = False) -> str:
    """
    Obtiene un access_token vía OAuth2 Client-Credentials, con caching in-memory
    para reutilizar el token hasta su expiración, a menos que force_refresh=True.
    """
    settings = ConfiguracionAPI.objects.filter(entorno='production').values(
        'TOKEN_URL', 'CLIENT_ID', 'CLIENT_SECRET', 'SCOPE', 'TIMEOUT_REQUEST'
    ).first()
    TOKEN_URL = settings['TOKEN_URL']
    CLIENT_ID = settings['CLIENT_ID']
    CLIENT_SECRET = settings['CLIENT_SECRET']
    SCOPE = settings['SCOPE']
    TIMEOUT = settings['TIMEOUT_REQUEST']

    cache_key = (CLIENT_ID, SCOPE)
    entry = _access_token_cache.get(cache_key)
    if not force_refresh and entry:
        if now() < entry['expires_at']:
            registrar_log(payment_id, tipo_log='AUTH', extra_info="Reutilizando Access Token cacheado")
            return entry['token']

    # Preparar request
    data = {'grant_type': 'client_credentials', 'scope': SCOPE}
    body = urlencode(data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    registrar_log(payment_id, tipo_log='AUTH', extra_info="Obteniendo nuevo Access Token")
    registrar_log(payment_id, tipo_log='AUTH', headers_enviados=headers, request_body=body)

    try:
        resp = requests.post(
            TOKEN_URL,
            data=body,
            headers=headers,
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=TIMEOUT
        )
        registrar_log(payment_id, tipo_log='AUTH', response_headers=dict(resp.headers), response_text=resp.text)
        resp.raise_for_status()
    except requests.RequestException as e:
        err = str(e)
        registrar_log(payment_id, tipo_log='ERROR', error=err, extra_info="Error de red al obtener Access Token")
        raise
    except Exception as e:
        err = str(e)
        registrar_log(payment_id, tipo_log='ERROR', error=err, extra_info="Error inesperado al obtener Access Token")
        raise

    payload = resp.json()
    token = payload.get('access_token')
    if not token:
        err = payload.get('error_description', 'Sin access_token en respuesta')
        registrar_log(payment_id, tipo_log='AUTH', error=err, extra_info="Token inválido recibido")
        raise Exception(f"Token inválido: {err}")

    # Cachear token hasta su expiración menos 5 segundos de margen
    expires_in = payload.get('expires_in', 0)
    expires_at = now() + timedelta(seconds=expires_in - 5)
    _access_token_cache[cache_key] = {
        'token': token,
        'expires_at': expires_at
    }
    registrar_log(payment_id, tipo_log='AUTH', extra_info="Token obtenido y cacheado correctamente")
    return token


def get_access_token_jwt(payment_id: str, force_refresh: bool = False) -> str:
    settings = get_settings()
    TOKEN_URL = settings["TOKEN_URL"]
    SCOPE = settings["SCOPE"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    registrar_log(payment_id, tipo_log='AUTH', extra_info="Obteniendo Access Token (JWT Assertion)")
    now = int(time.time())
    payload = {
        'iss': transfer.client.clientId,
        'sub': transfer.client.clientId,
        'aud': TOKEN_URL,
        'iat': now,
        'exp': now + TIMEOUT_REQUEST
    }
    private_key, kid = load_private_key_y_kid()
    assertion = jwt.encode(payload, private_key, algorithm='ES256', headers={'kid': kid})
    data = {
        'grant_type': 'client_credentials',
        'scope': SCOPE,
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': assertion
    }
    registrar_log(payment_id, tipo_log='AUTH', request_body=data)
    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=TIMEOUT_REQUEST)
        registrar_log(payment_id, tipo_log='AUTH', response_headers=dict(resp.headers), response_text=resp.text)
        resp.raise_for_status()
    except Exception as e:
        err = str(e)
        registrar_log(payment_id, tipo_log='ERROR', error=err, extra_info="Error obteniendo Access Token JWT")
        raise
    token = resp.json().get('access_token')
    if not token:
        err = resp.json().get('error_description', 'Sin access_token en respuesta')
        registrar_log(payment_id, tipo_log='AUTH', error=err, extra_info="Token JWT inválido")
        raise Exception(f"Token JWT inválido: {err}")
    registrar_log(payment_id, tipo_log='AUTH', extra_info="Token JWT obtenido correctamente")
    return token


def update_sca_request(transfer: Transfer, action: str, otp: str, token: str) -> requests.Response:
    settings = get_settings()
    API_URL = settings["API_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    url = f"{API_URL}/{transfer.payment_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Id': transfer.payment_id,
        'Correlation-Id': transfer.payment_id
    }
    payload = {'action': action, 'authId': transfer.auth_id}
    registrar_log(transfer.payment_id, tipo_log='SCA', headers_enviados=headers, request_body=payload, extra_info="Actualizando SCA")
    resp = requests.patch(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(transfer.payment_id, tipo_log='SCA', response_headers=dict(resp.headers), response_text=resp.text, extra_info="Respuesta SCA")
    resp.raise_for_status()
    data = resp.json()
    transfer.auth_id = data.get('authId')
    transfer.status = data.get('transactionStatus', transfer.status)
    transfer.save()
    registrar_log(transfer.payment_id, tipo_log='SCA', extra_info=f"Actualización exitosa: {transfer.status}")
    return resp


def fetch_transfer_details(transfer: Transfer, token: str) -> dict:
    settings = get_settings()
    API_URL = settings["API_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    url = f"{API_URL}/{transfer.payment_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Idempotency-Id': transfer.payment_id,
        'Correlation-Id': transfer.payment_id
    }
    registrar_log(transfer.payment_id, tipo_log='TRANSFER', headers_enviados=headers, extra_info="Obteniendo estado de transferencia")
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_REQUEST)
    registrar_log(transfer.payment_id, tipo_log='TRANSFER', response_headers=dict(resp.headers), response_text=resp.text, extra_info="Respuesta fetch status")
    resp.raise_for_status()
    data = resp.json()
    transfer.status = data.get('transactionStatus', transfer.status)
    transfer.save()
    xml_path = generar_xml_pain002(data, transfer.payment_id)
    validar_xml_con_xsd(xml_path, xsd_path="schemas/xsd/pain.002.001.03.xsd")
    registrar_log(transfer.payment_id, tipo_log='XML', extra_info="Pain002 generado y validado")
    return data


def get_client_credentials_token():
    settings = get_settings()
    SCOPE = settings["SCOPE"]
    CLIENT_ID = settings["CLIENT_ID"]
    CLIENT_SECRET = settings["CLIENT_SECRET"]
    TOKEN_URL = settings["TOKEN_URL"]
    TIMEOUT = settings["TIMEOUT"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    data = {
        'grant_type': 'client_credentials',
        'scope': SCOPE,
    }
    auth = (CLIENT_ID, CLIENT_SECRET)
    registrar_log("CLIENT_CRED", tipo_log='AUTH', request_body=data, extra_info="Solicitando token Client Credentials")
    try:
        resp = requests.post(TOKEN_URL, data=data, auth=auth, timeout=TIMEOUT)
        registrar_log("CLIENT_CRED", tipo_log='AUTH', response_headers=dict(resp.headers), response_text=resp.text, extra_info="Token recibido Client Credentials")
        resp.raise_for_status()
        token_data = resp.json()
        registrar_log("CLIENT_CRED", tipo_log='AUTH', extra_info="Token obtenido con éxito")
        return token_data['access_token'], token_data.get('expires_in', TIMEOUT_REQUEST)
    except Exception as e:
        registrar_log("CLIENT_CRED", tipo_log='ERROR', error=str(e), extra_info="Error al obtener token Client Credentials")
        raise


def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b'=').decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return verifier, challenge


def build_auth_url(state, code_challenge):
    p = get_settings()["OAUTH2"]
    return (
        f"{p['AUTHORIZE_URL']}?response_type=code"
        f"&client_id={p['CLIENT_ID']}"
        f"&redirect_uri={p['REDIRECT_URI']}"
        f"&scope={p['SCOPE']}"
        f"&state={state}"
        f"&code_challenge_method=S256"
        f"&code_challenge={code_challenge}"
    )


def fetch_token_by_code(code, code_verifier):
    p = get_settings()["OAUTH2"]
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': p['REDIRECT_URI'],
        'code_verifier': code_verifier
    }
    auth = (p['CLIENT_ID'], p['CLIENT_SECRET'])
    resp = requests.post(p['TOKEN_URL'], data=data, auth=auth, timeout=p['TIMEOUT_REQUEST'])
    resp.raise_for_status()
    j = resp.json()
    return j['access_token'], j.get('refresh_token'), j.get('expires_in', p['TIMEOUT_REQUEST'])


def refresh_access_token(refresh_token: str) -> tuple[str, str, int]:
    p = get_settings()["OAUTH2"]
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    auth = (p['CLIENT_ID'], p['CLIENT_SECRET'])
    registrar_log("REFRESH_TOKEN", tipo_log='AUTH', request_body=data, extra_info="Iniciando refresh token OAuth2")
    try:
        resp = requests.post(p['TOKEN_URL'], data=data, auth=auth, timeout=p['TIMEOUT_REQUEST'])
        registrar_log("REFRESH_TOKEN", tipo_log='AUTH', response_headers=dict(resp.headers), response_text=resp.text, extra_info="Respuesta refresh token")
        resp.raise_for_status()
        j = resp.json()
        registrar_log("REFRESH_TOKEN", tipo_log='AUTH', extra_info="Token refrescado correctamente")
        return j['access_token'], j.get('refresh_token'), j.get('expires_in', p['TIMEOUT_REQUEST'])
    except Exception as e:
        registrar_log("REFRESH_TOKEN", tipo_log='ERROR', error=str(e), extra_info="Error al refrescar token OAuth2")
        raise




# ===========================
# OTP
# ===========================
# ===========================
# OTP Helper
# ===========================

def _challenge_url(auth_url: str) -> str:
    """
    Asegura que la URL base de autorización de desafíos termine en '/challenges'.
    """
    return auth_url.rstrip('/') + '/challenges'

# ===========================
# MTAN Challenge
# ===========================
def crear_challenge_mtanA(transfer: Transfer, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Id': payment_id,
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'MTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'challenge': {
            'mobilePhoneNumber': transfer.debtor.mobile_phone_number
        }
    }
    registrar_log(payment_id, headers_enviados=headers, request_body=payload, extra_info="Iniciando MTAN challenge", tipo_log='OTP')
    
    resp = requests.post(AUTH_URL, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, response_headers=dict(resp.headers), response_text=resp.text, tipo_log='OTP')
    resp.raise_for_status()
    return resp.json()['id']

def crear_challenge_mtan(transfer: Transfer, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'MTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'language': 'en',
        'challenge': {
            'mobilePhoneNumber': transfer.debtor.mobile_phone_number
        }
    }
    registrar_log(payment_id, headers_enviados=headers, request_body=payload,
                 extra_info="Iniciando MTAN challenge", tipo_log='OTP')

    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, response_headers=dict(resp.headers), response_text=resp.text, tipo_log='OTP')
    resp.raise_for_status()
    return resp.json()['id']

# ---------------------------

def verify_mtanA(challenge_id: str, otp: str, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {'challengeResponse': otp}
    registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers, request_body=payload, extra_info=f"Verificando OTP para challenge {challenge_id}")
    r = requests.patch(f"{AUTH_URL}/{challenge_id}", headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, tipo_log='OTP', response_headers=dict(r.headers), response_text=r.text, extra_info="Respuesta verificación OTP")
    r.raise_for_status()
    return r.json()['challengeProofToken']

def verify_mtan(challenge_id: str, otp: str, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL) + f"/{challenge_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {'challengeResponse': otp}
    registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers,
                 request_body=payload, extra_info=f"Verificando OTP para challenge {challenge_id}")

    resp = requests.patch(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, tipo_log='OTP', response_headers=dict(resp.headers),
                 response_text=resp.text, extra_info="Respuesta verificación OTP")
    resp.raise_for_status()
    return resp.json()['challengeProofToken']




# ===========================
# PhotoTAN Challenge
# ===========================
def crear_challenge_phototanA(transfer: Transfer, token: str, payment_id: str):
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Id': payment_id,
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'PHOTOTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'challenge': {}
    }
    registrar_log(payment_id, headers_enviados=headers, request_body=payload, extra_info="Iniciando PhotoTAN challenge", tipo_log='OTP')
    resp = requests.post(AUTH_URL, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, response_headers=dict(resp.headers), response_text=resp.text, tipo_log='OTP')
    resp.raise_for_status()
    data = resp.json()
    return data['id'], data.get('imageBase64')

def crear_challenge_phototan(transfer: Transfer, token: str, payment_id: str) -> tuple:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'PHOTOTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'language': 'en',
        'challenge': {}
    }
    registrar_log(payment_id, headers_enviados=headers, request_body=payload,
                 extra_info="Iniciando PhotoTAN challenge", tipo_log='OTP')

    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, response_headers=dict(resp.headers),
                 response_text=resp.text, tipo_log='OTP')
    resp.raise_for_status()
    data = resp.json()
    return data['id'], data.get('imageBase64')

# ---------------------------


def verify_phototanA(challenge_id: str, otp: str, token: str, payment_id: str) -> str:
    return verify_mtan(challenge_id, otp, token, payment_id)

def verify_phototan(challenge_id: str, otp: str, token: str, payment_id: str) -> str:
    """
    Verifica la PhotoTAN usando PATCH al endpoint de challenge con el OTP proporcionado.
    """
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL) + f"/{challenge_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {'challengeResponse': otp}
    registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers,
                 request_body=payload, extra_info=f"Verificando PhotoTAN para challenge {challenge_id}")

    resp = requests.patch(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, tipo_log='OTP', response_headers=dict(resp.headers),
                 response_text=resp.text, extra_info="Respuesta verificación PhotoTAN")
    resp.raise_for_status()
    return resp.json().get('challengeProofToken') or resp.json().get('otp')



# ===========================
# PushTAN Challenge
# ===========================
def crear_challenge_pushtanA(transfer: Transfer, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    schema_data = transfer.to_schema_data()
    request_data = {
        "type": "challengeRequestDataSepaPaymentTransfer",
        "targetIban": schema_data["creditorAccount"]["iban"],
        "amountCurrency": schema_data["instructedAmount"]["currency"],
        "amountValue": schema_data["instructedAmount"]["amount"]
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'PUSHTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'requestData': request_data,
        'language': 'de'
    }
    registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers, request_body=payload, extra_info="Iniciando PushTAN challenge")
    response = requests.post(AUTH_URL, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, tipo_log='OTP', response_headers=dict(response.headers), response_text=response.text)
    response.raise_for_status()
    return response.json()['id']

def crear_challenge_pushtan(transfer: Transfer, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    schema_data = transfer.to_schema_data()
    request_data = {
        'type': 'challengeRequestDataSepaPaymentTransfer',
        'targetIban': schema_data['creditorAccount']['iban'],
        'amountCurrency': schema_data['instructedAmount']['currency'],
        'amountValue': schema_data['instructedAmount']['amount']
    }
    url = _challenge_url(AUTH_URL)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': payment_id
    }
    payload = {
        'method': 'PUSHTAN',
        'requestType': 'SEPA_TRANSFER_GRANT',
        'requestData': request_data,
        'language': 'de'
    }
    registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers,
                 request_body=payload, extra_info="Iniciando PushTAN challenge")

    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
    registrar_log(payment_id, tipo_log='OTP', response_headers=dict(resp.headers),
                 response_text=resp.text)
    resp.raise_for_status()
    return resp.json()['id']

# ---------------------------

def resolver_challenge_pushtanA(challenge_id: str, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Correlation-Id': payment_id
    }
    start = time.time()
    while True:
        response = requests.get(f"{AUTH_URL}/{challenge_id}", headers=headers, timeout=TIMEOUT_REQUEST)
        registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers, response_headers=dict(response.headers), response_text=response.text, extra_info="Esperando validación PushTAN")
        data = response.json()
        status = data.get('status')
        if status == 'VALIDATED':
            otp = data.get('otp')
            registrar_log(payment_id, tipo_log='AUTH', extra_info=f"OTP PushTAN validado: {otp}")
            return otp
        if status in ('EXPIRED', 'REJECTED', 'EIDP_ERROR'):
            msg = f"PushTAN fallido: {status}"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise Exception(msg)
        if time.time() - start > 300:
            msg = "Timeout esperando VALIDATED PushTAN"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise TimeoutError(msg)
        time.sleep(1)

def resolver_challenge_pushtan(challenge_id: str, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL) + f"/{challenge_id}"
    start = time.time()
    while True:
        resp = requests.get(url, headers={
            'Authorization': f'Bearer {token}',
            'Correlation-Id': payment_id
        }, timeout=TIMEOUT_REQUEST)
        registrar_log(payment_id, tipo_log='OTP', headers_enviados=resp.request.headers,
                     response_headers=dict(resp.headers), response_text=resp.text,
                     extra_info="Esperando validación PushTAN")
        data = resp.json()
        status = data.get('status')
        if status == 'VALIDATED':
            otp = data.get('otp')
            registrar_log(payment_id, tipo_log='OTP', extra_info=f"OTP PushTAN validado: {otp}")
            return otp
        if status in ('EXPIRED', 'REJECTED', 'EIDP_ERROR'):
            msg = f"PushTAN fallido: {status}"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise Exception(msg)
        if time.time() - start > 300:
            msg = "Timeout esperando VALIDATED PushTAN"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise TimeoutError(msg)
        time.sleep(1)



# ===========================
# Generic Challenge Resolver
# ===========================
def resolver_challengeA(challenge_id: str, token: str, payment_id: str) -> str:
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Correlation-Id': payment_id
    }
    start = time.time()
    while True:
        resp = requests.get(f"{AUTH_URL}/{challenge_id}", headers=headers, timeout=TIMEOUT_REQUEST)
        registrar_log(payment_id, tipo_log='OTP', headers_enviados=headers, response_headers=dict(resp.headers), response_text=resp.text, extra_info=f"Comprobando estado challenge {challenge_id}")
        data = resp.json()
        status = data.get('status')
        if status == 'VALIDATED':
            otp = data.get('otp')
            registrar_log(payment_id, extra_info=f"OTP validado: {otp}", tipo_log='AUTH')
            return otp
        if status in ('EXPIRED', 'REJECTED', 'EIDP_ERROR'):
            msg = f"Challenge fallido: {status}"
            registrar_log(payment_id, error=msg, tipo_log='ERROR')
            raise Exception(msg)
        if time.time() - start > 300:
            msg = "Timeout esperando VALIDATED"
            registrar_log(payment_id, error=msg, tipo_log='ERROR')
            raise TimeoutError(msg)
        time.sleep(1)

def resolver_challenge(challenge_id: str, token: str, payment_id: str) -> str:
    """
    Polling genérico para cualquier challenge creado. Solo para usos alternativos.
    """
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]

    url = _challenge_url(AUTH_URL) + f"/{challenge_id}"
    start = time.time()
    while True:
        resp = requests.get(url, headers={
            'Authorization': f'Bearer {token}',
            'Correlation-Id': payment_id
        }, timeout=TIMEOUT_REQUEST)
        registrar_log(payment_id, tipo_log='OTP', headers_enviados=resp.request.headers,
                     response_headers=dict(resp.headers), response_text=resp.text,
                     extra_info=f"Comprobando estado challenge {challenge_id}")
        data = resp.json()
        status = data.get('status')
        if status == 'VALIDATED':
            otp = data.get('otp')
            registrar_log(payment_id, extra_info=f"OTP validado: {otp}", tipo_log='OTP')
            return otp
        if status in ('EXPIRED', 'REJECTED', 'EIDP_ERROR'):
            msg = f"Challenge fallido: {status}"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise Exception(msg)
        if time.time() - start > 300:
            msg = "Timeout esperando VALIDATED"
            registrar_log(payment_id, tipo_log='ERROR', error=msg)
            raise TimeoutError(msg)
        time.sleep(1)



# ===========================
# Automatic OTP Retrieval
# ===========================
def obtener_otp_automaticoA(transfer: Transfer):
    token = get_access_token(transfer.payment_id)
    challenge_id = crear_challenge_pushtan(transfer, token, transfer.payment_id)
    otp = resolver_challenge(challenge_id, token, transfer.payment_id)
    registrar_log(transfer.payment_id, tipo_log='OTP', extra_info="OTP obtenido automáticamente")
    return otp, token

def obtener_otp_automatico(transfer: Transfer) -> tuple:
    token = get_access_token(transfer.payment_id)
    challenge_id = crear_challenge_pushtan(transfer, token, transfer.payment_id)
    otp = resolver_challenge_pushtan(challenge_id, token, transfer.payment_id)
    registrar_log(transfer.payment_id, tipo_log='OTP', extra_info="OTP obtenido automáticamente")
    return otp, token

# ---------------------------

def obtener_otp_automatico_con_challengeA(transfer):
    token = get_access_token(transfer.payment_id)
    challenge_id = crear_challenge_autorizacion(transfer, token, transfer.payment_id)
    otp_token = resolver_challenge(challenge_id, token, transfer.payment_id)
    return otp_token, token

def obtener_otp_automatico_con_challenge(transfer: Transfer) -> tuple:
    token = get_access_token(transfer.payment_id)
    challenge_id = crear_challenge_autorizacion(transfer, token, transfer.payment_id)
    otp_token = resolver_challenge_pushtan(challenge_id, token, transfer.payment_id)
    registrar_log(transfer.payment_id, tipo_log='OTP', extra_info="OTP obtenido automáticamente con challenge personalizado")
    return otp_token, token

# ---------------------------
# ===========================



def preparar_request_type_y_datos(schema_data):
    request_type = "SEPA_TRANSFER_GRANT"
    datos = {
        "type": "challengeRequestDataSepaPaymentTransfer",
        "targetIban": schema_data["creditorAccount"]["iban"],
        "amountCurrency": schema_data["instructedAmount"]["currency"],
        "amountValue": schema_data["instructedAmount"]["amount"]
    }
    return request_type, datos

def crear_challenge_autorizacion(transfer, token):
    settings = get_settings()
    AUTH_URL = settings["AUTH_URL"]
    TIMEOUT_REQUEST = settings["TIMEOUT_REQUEST"]
    
    pid = transfer.payment_id
    try:
        registrar_log(pid, extra_info="Iniciando challenge OTP", tipo_log='OTP')
        payload = {
            'method':'PUSHTAN','requestType':'SEPA_TRANSFER_GRANT',
            'requestData':{
                'type':'challengeRequestDataSepaPaymentTransfer',
                'targetIban':transfer.creditor_account.iban,
                'amountCurrency':transfer.currency,
                'amountValue':float(transfer.instructed_amount)
            },'language':'de'
        }
        headers = {'Authorization':f'Bearer {token}','Content-Type':'application/json'}
        registrar_log(pid, headers_enviados=headers, request_body=payload, tipo_log='OTP')
        resp = requests.post(AUTH_URL, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
        registrar_log(pid, response_text=resp.text, tipo_log='OTP')
        resp.raise_for_status()
        cid = resp.json().get('id')
        registrar_log(pid, extra_info=f"Challenge creado con ID {cid}", tipo_log='OTP')
        return cid
    except Exception as e:
        registrar_log(pid, error=str(e), extra_info="Error al crear challenge", tipo_log='ERROR')
        raise




from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from api.gpt4.models import ClaveGenerada, Transfer
import time
import jwt
from api.configuraciones_api.helpers import get_conf, get_conf_keys
from api.gpt4.utils import registrar_log


def load_private_key_y_kid(registro=None):
    try:
        clave = ClaveGenerada.objects.filter(estado="EXITO").order_by('-fecha').first()
        if not clave:
            raise ValueError("No se encontró ninguna clave válida con estado EXITO.")

        if not clave.clave_privada or not clave.kid:
            raise ValueError("La clave encontrada no contiene 'clave_privada' o 'kid'.")

        registrar_log(
            registro=registro,
            tipo_log='AUTH',
            extra_info=f"✅ Clave y KID cargados correctamente (KID={clave.kid})"
        )
        return clave.clave_privada, clave.kid

    except Exception as e:
        registrar_log(
            registro=registro,
            tipo_log='ERROR',
            error=str(e),
            extra_info="❌ Error cargando clave y kid"
        )
        raise

def generar_client_assertion(registro=None):
    try:
        conf = get_conf()
        client_id = conf.get("CLIENT_ID")
        token_url = conf.get("TOKEN_URL")

        if not client_id or not token_url:
            raise ValueError("CLIENT_ID o TOKEN_URL no están configurados correctamente.")

        private_key, kid = load_private_key_y_kid(registro=registro)

        issued_at = int(time.time())
        expiration = issued_at + 300  # 5 minutos

        payload = {
            "iss": client_id,
            "sub": client_id,
            "aud": token_url,
            "jti": f"{client_id}-{issued_at}",
            "exp": expiration,
            "iat": issued_at,
        }

        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": kid
        }

        assertion = jwt.encode(
            payload,
            private_key,
            algorithm="RS256",
            headers=headers
        )

        registrar_log(
            registro=registro,
            tipo_log='AUTH',
            extra_info=f"✅ JWT generado correctamente para client_id={client_id}, kid={kid}"
        )
        return assertion

    except Exception as e:
        registrar_log(
            registro=registro,
            tipo_log='ERROR',
            error=str(e),
            extra_info="❌ Error generando client_assertion"
        )
        raise


