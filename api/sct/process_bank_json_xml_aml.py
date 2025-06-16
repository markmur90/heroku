from datetime import datetime
from dotenv import load_dotenv
import os
import logging

import requests

from api.sct.generate_xml2 import generate_sepa_xml2
from api.sct.models import SepaCreditTransferDetailsResponse
from config import settings

# Configurar el logger
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def process_bank_transfer_json_xml_aml(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria enviando datos JSON, XML y AML al banco.
    """
    try:
        # Validar variables de entorno necesarias
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        if not all([access_token, psu_id, psu_ip_address]):
            logger.error("Faltan variables de entorno necesarias para la solicitud.")
            logger.debug(f"ACCESS_TOKEN: {access_token}")
            logger.debug(f"PSU_ID: {psu_id}")
            logger.debug(f"PSU_IP_ADDRESS: {psu_ip_address}")
            return {"error": "Faltan variables de entorno necesarias para la solicitud"}
        
        # Rutas de los archivos XML y AML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        aml_path = os.path.join(settings.MEDIA_ROOT, f"AMLTransactionReport_{transfers.idempotency_key}.xml")

        # Generar el archivo XML si no existe
        if not os.path.exists(xml_path):
            try:
                sepa_xml = generate_sepa_xml2(transfers)
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

        # Leer el contenido del archivo AML
        try:
            with open(aml_path, "r", encoding="utf-8") as aml_file:
                aml_content = aml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo AML: {str(e)}", exc_info=True)
            return {"error": "Error al leer el archivo AML"}

        # Construir los datos JSON de la transferencia
        json_data = {
            "purposeCode": transfers.purpose_code,
            "requestedExecutionDate": transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.debtor_adress_zip_code_and_city,
                    "country": transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfers.debtor_account_iban,
                "bic": transfers.debtor_account_bic,
                "currency": transfers.debtor_account_currency
            },
            "creditor": {
                "name": transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.creditor_adress_zip_code_and_city,
                    "country": transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfers.creditor_account_iban,
                "bic": transfers.creditor_account_bic,
                "currency": transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfers.payment_identification_end_to_end_id),
                "instructionId": transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount": str(transfers.instructed_amount),
                "currency": transfers.instructed_currency
            },
            "remittanceInformationStructured": transfers.remittance_information_structured,
            "remittanceInformationUnstructured": transfers.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
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
                json=json_data
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar la solicitud al banco: {str(e)}", exc_info=True)
            return {"error": "Error al enviar la solicitud al banco"}

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return {"error": f"Error al enviar la solicitud al banco: {response.text}"}

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
        logger.error(f"Error inesperado en process_bank_transfer_json_xml_aml para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}


def process_bank_transfer_jsonn(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria enviando solo datos JSON al banco.
    """
    try:
        # Validar variables de entorno necesarias
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        if not all([access_token, psu_id, psu_ip_address]):
            logger.error("Faltan variables de entorno necesarias para la solicitud.")
            logger.debug(f"ACCESS_TOKEN: {access_token}")
            logger.debug(f"PSU_ID: {psu_id}")
            logger.debug(f"PSU_IP_ADDRESS: {psu_ip_address}")
            return {"error": "Faltan variables de entorno necesarias para la solicitud"}

        # Construir los datos JSON de la transferencia
        json_data = {
            "purposeCode": transfers.purpose_code,
            "requestedExecutionDate": transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.debtor_adress_zip_code_and_city,
                    "country": transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfers.debtor_account_iban,
                "bic": transfers.debtor_account_bic,
                "currency": transfers.debtor_account_currency
            },
            "creditor": {
                "name": transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.creditor_adress_zip_code_and_city,
                    "country": transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfers.creditor_account_iban,
                "bic": transfers.creditor_account_bic,
                "currency": transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfers.payment_identification_end_to_end_id),
                "instructionId": transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount": str(transfers.instructed_amount),
                "currency": transfers.instructed_currency
            },
            "remittanceInformationStructured": transfers.remittance_information_structured,
            "remittanceInformationUnstructured": transfers.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        try:
            response = requests.post(
                url=f"{settings.DEUTSCHE_BANK_API_URL}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "idempotency-id": str(idempotency_key),
                    "otp": "SEPA_TRANSFER_GRANT",
                    "X-Request-ID": f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
                    "PSU-ID": psu_id,
                    "PSU-IP-Address": psu_ip_address,
                },
                json=json_data
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar la solicitud al banco: {str(e)}", exc_info=True)
            return {"error": "Error al enviar la solicitud al banco"}

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return {"error": f"Error al enviar la solicitud al banco: {response.text}"}

        # Procesar la respuesta del banco
        try:
            bank_response = response.json()  # Asumiendo que la respuesta es JSON
            return {"success": True, "bank_response": bank_response}
        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return {"error": "Error procesando la respuesta del banco"}

    except Exception as e:
        logger.error(f"Error inesperado en process_bank_transfer_json para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}


