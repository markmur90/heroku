import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from api.gpt3.helpers import obtener_ruta_schema_transferencia

logger = logging.getLogger("bank_services")


def generar_archivo_aml(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
    aml_filename = f"aml_{payment_id}.xml"
    aml_path = os.path.join(carpeta_transferencia, aml_filename)

    root = ET.Element("AMLTransactionReport")
    transaction = ET.SubElement(root, "Transaction")

    ET.SubElement(transaction, "TransactionID").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(transaction, "TransactionType").text = "INST"
    ET.SubElement(transaction, "ExecutionDate").text = transferencia.requested_execution_date.strftime("%Y-%m-%dT%H:%M:%S")

    amount = ET.SubElement(transaction, "Amount")
    amount.set("currency", transferencia.instructed_amount.currency)
    amount.text = str(transferencia.instructed_amount.amount)

    debtor = ET.SubElement(transaction, "Debtor")
    ET.SubElement(debtor, "Name").text = transferencia.debtor.debtor_name
    ET.SubElement(debtor, "IBAN").text = transferencia.debtor_account.iban
    ET.SubElement(debtor, "Country").text = transferencia.debtor.postal_address.country
    ET.SubElement(debtor, "CustomerID").text = transferencia.debtor.customer_id
    ET.SubElement(debtor, "KYCVerified").text = "true"

    creditor = ET.SubElement(transaction, "Creditor")
    ET.SubElement(creditor, "Name").text = transferencia.creditor.creditor_name
    ET.SubElement(creditor, "IBAN").text = transferencia.creditor_account.iban
    ET.SubElement(creditor, "BIC").text = transferencia.creditor_agent.financial_institution_id
    ET.SubElement(creditor, "Country").text = transferencia.creditor.postal_address.country

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
    return aml_path


