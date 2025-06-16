from rest_framework.exceptions import APIException
import logging  # Importar el módulo de logging
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from config import settings
import requests
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics

from api.sct.process_deutsche_bank import deutsche_bank_transfer, deutsche_bank_transfer11
from api.sct.models import SepaCreditTransferDetailsResponse, SepaCreditTransferRequest
from api.sct.serializers import SepaCreditTransferRequestSerializer
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml

from dotenv import load_dotenv
load_dotenv()


# Configurar el logger
logger = logging.getLogger(__name__)

# Constantes
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def process_bank_transfer_json(transfers, idempotency_key):
    """
    Procesa una transferencia bancaria exclusivamente para Deutsche Bank.
    """
    try:
        response = deutsche_bank_transfer11(idempotency_key, transfers)
        if "error" not in response:
            return {
                "transaction_status": "ACCP",
                "payment_id":str(transfers.payment_id),
                "auth_id":str(transfers.auth_id),
                "bank_response": response,
            }
        return response
    except Exception as e:
        logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
        raise APIException("Error procesando la transferencia bancaria.")


def process_bank_transfer(idempotency_key, transfers):
    try:
        # Ruta del archivo XML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        if not os.path.exists(xml_path):
            raise FileNotFoundError(f"El archivo XML {xml_path} no existe.")

        # Generar el archivo XML si no existe
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        if not os.path.exists(xml_path):
            sepa_xml = generate_sepa_xml(transfers)
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

        # Leer el contenido del archivo XML
        with open(xml_path, "r") as xml_file:
            xml_content = xml_file.read()

        # Enviar el XML al banco
        response = requests.post(
            url=f"{settings.DEUTSCHE_BANK_API_URL}",
            headers={"Content-Type": "application/xml"},
            data=xml_content
        )

        # Verificar la respuesta del banco
        if response.status_code != 200:
            return {"error": f"Error al enviar el XML al banco: {response.text}"}

        # Procesar la respuesta del banco (asumiendo que es XML)
        bank_response = response.text
        return {"success": True, "bank_response": bank_response}

    except Exception as e:
        logger.error(f"Error en process_bank_transfer: {str(e)}", exc_info=True)
        return {"error": str(e)}


def process_bank_transfer_xml(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando un archivo XML generado para SEPA.
    """
    try:
        # Ruta del archivo XML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")

        # Generar el archivo XML si no existe
        if not os.path.exists(xml_path):
            try:
                sepa_xml = generate_sepa_xml(transfers)
                with open(xml_path, "w", encoding="utf-8") as xml_file:
                    os.chmod(xml_path, 0o600)  # Permisos restrictivos
                    xml_file.write(sepa_xml)
            except Exception as e:
                logger.error(f"Error al generar o guardar el archivo XML: {str(e)}", exc_info=True)
                return {"error": "Error al generar el archivo XML"}

        # Leer el contenido del archivo XML
        try:
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo XML: {str(e)}", exc_info=True)
            return {"error": "Error al leer el archivo XML"}

        # Enviar el XML al banco
        try:
            response = requests.post(
                url=settings.BANK_API_URL,
                headers={"Content-Type": "application/xml"},
                data=xml_content
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar el XML al banco: {str(e)}", exc_info=True)
            return {"error": "Error al enviar el XML al banco"}

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return {"error": f"Error al enviar el XML al banco: {response.text}"}

        # Procesar la respuesta del banco
        try:
            bank_response = response.text  # Asumiendo que es texto o XML
            return {"success": True, "bank_response": bank_response}
        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return {"error": "Error procesando la respuesta del banco"}

    except Exception as e:
        logger.error(f"Error inesperado en process_bank_transfer para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}


def process_bank_transfer_xml2(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando un archivo XML generado para SEPA.
    """
    try:
        # Ruta del archivo XML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        aml_path = os.path.join(settings.MEDIA_ROOT, f"AMLTransactionReport_{transfers.idempotency_key}.xml")

        # Leer el contenido del archivo XML
        try:
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo XML: {str(e)}", exc_info=True)
            return {"error": "Error al leer el archivo XML"}

        # Leer el contenido del archivo AML
        try:
            with open(aml_path, "r", encoding="utf-8") as aml_file:
                aml_content = aml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo AML: {str(e)}", exc_info=True)
            return {"error": "Error al leer el archivo AML"}

        # Validar variables de entorno necesarias
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        if not all([access_token, psu_id, psu_ip_address]):
            logger.error("Faltan variables de entorno necesarias para la solicitud.")
            return {"error": "Faltan variables de entorno necesarias para la solicitud"}

        # Enviar el XML al banco
        try:
            response = requests.post(
                url=f"{settings.DEUTSCHE_BANK_API_URL}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/xml",
                    "idempotency-id": str(idempotency_key),
                    "otp": "SEPA_TRANSFER_GRANT",
                    "X-Request-ID": f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
                    "PSU-ID": psu_id,
                    "PSU-IP-Address": psu_ip_address,
                },
                data=f"{xml_content}\n{aml_content}",
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar el XML al banco: {str(e)}", exc_info=True)
            return {"error": "Error al enviar el XML al banco"}

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return {"error": f"Error al enviar el XML al banco: {response.text}"}

        # Procesar la respuesta del banco
        try:
            bank_response = response.text  # Asumiendo que es texto o XML
            # Actualizar detalles de la transferencia en la base de datos
            SepaCreditTransferDetailsResponse.objects.update_or_create(
                payment_id=transfers,
                defaults={
                    "transaction_status": "ACCP",  # Estado actualizado según el banco
                    "purpose_code": transfers.purpose_code,
                    "requested_execution_date": transfers.requested_execution_date,
                    "debtor_name": transfers.debtor_name,
                    "debtor_adress_street_and_house_number": transfers.debtor_adress_street_and_house_number,
                    "debtor_adress_zip_code_and_city": transfers.debtor_adress_zip_code_and_city,
                    "debtor_adress_country": transfers.debtor_adress_country,
                    "debtor_account_iban": transfers.debtor_account_iban,
                    "debtor_account_bic": transfers.debtor_account_bic,
                    "debtor_account_currency": transfers.debtor_account_currency,
                    "creditor_name": transfers.creditor_name,
                    "creditor_adress_street_and_house_number": transfers.creditor_adress_street_and_house_number,
                    "creditor_adress_zip_code_and_city": transfers.creditor_adress_zip_code_and_city,
                    "creditor_adress_country": transfers.creditor_adress_country,
                    "creditor_account_iban": transfers.creditor_account_iban,
                    "creditor_account_bic": transfers.creditor_account_bic,
                    "creditor_account_currency": transfers.creditor_account_currency,
                    "creditor_agent_financial_institution_id": transfers.creditor_agent_financial_institution_id,
                    "payment_identification_end_to_end_id": transfers.payment_identification_end_to_end_id,
                    "payment_identification_instruction_id": transfers.payment_identification_instruction_id,
                    "instructed_amount": transfers.instructed_amount,
                    "instructed_currency": transfers.instructed_currency,
                    "remittance_information_structured": transfers.remittance_information_structured,
                    "remittance_information_unstructured": transfers.remittance_information_unstructured,
                },
            )
            return {"success": True, "bank_response": bank_response}
        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return {"error": "Error procesando la respuesta del banco"}

    except Exception as e:
        logger.error(f"Error inesperado en process_bank_transfer_xml2 para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}
    
