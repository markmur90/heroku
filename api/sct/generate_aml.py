import logging
import xml.etree.ElementTree as ET
from datetime import datetime
logger = logging.getLogger("bank_services")


def generate_aml_transaction_report(transfers, file_path):
    """
    Genera un archivo AMLTransactionReport basado en los datos de transferencia proporcionados.
    """
    try:
        # Crear el elemento raíz
        root = ET.Element("AMLTransactionReport")

        # Crear el elemento Transaction
        transaction = ET.SubElement(root, "Transaction")

        # Agregar detalles de la transacción
        ET.SubElement(transaction, "TransactionID").text = transfers.get("transaction_id", "UNKNOWN")
        ET.SubElement(transaction, "TransactionType").text = transfers.get("transaction_type", "SEPA")
        ET.SubElement(transaction, "ExecutionDate").text = transfers.get("execution_date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        
        # Monto con atributo de moneda
        amount = ET.SubElement(transaction, "Amount")
        amount.set("currency", transfers.get("currency", "EUR"))
        amount.text = str(transfers.get("amount", 0.00))

        # Información del deudor
        debtor = ET.SubElement(transaction, "Debtor")
        ET.SubElement(debtor, "Name").text = transfers.get("debtor_name", "UNKNOWN")
        ET.SubElement(debtor, "IBAN").text = transfers.get("debtor_iban", "UNKNOWN")
        ET.SubElement(debtor, "BIC").text = transfers.get("debtor_bic", "UNKNOWN")
        ET.SubElement(debtor, "Country").text = transfers.get("debtor_country", "UNKNOWN")
        ET.SubElement(debtor, "CustomerID").text = transfers.get("debtor_customer_id", "UNKNOWN")
        ET.SubElement(debtor, "KYCVerified").text = str(transfers.get("debtor_kyc_verified", False)).lower()

        # Información del acreedor
        creditor = ET.SubElement(transaction, "Creditor")
        ET.SubElement(creditor, "Name").text = transfers.get("creditor_name", "UNKNOWN")
        ET.SubElement(creditor, "IBAN").text = transfers.get("creditor_iban", "UNKNOWN")
        ET.SubElement(creditor, "BIC").text = transfers.get("creditor_bic", "UNKNOWN")
        ET.SubElement(creditor, "Country").text = transfers.get("creditor_country", "UNKNOWN")

        # Otros detalles
        ET.SubElement(transaction, "Purpose").text = transfers.get("purpose", "UNKNOWN")
        ET.SubElement(transaction, "Channel").text = transfers.get("channel", "UNKNOWN")
        ET.SubElement(transaction, "RiskScore").text = str(transfers.get("risk_score", 0))
        ET.SubElement(transaction, "PEP").text = str(transfers.get("pep", False)).lower()
        ET.SubElement(transaction, "SanctionsCheck").text = transfers.get("sanctions_check", "UNKNOWN")
        ET.SubElement(transaction, "HighRiskCountry").text = str(transfers.get("high_risk_country", False)).lower()

        # Flags
        flags = ET.SubElement(transaction, "Flags")
        ET.SubElement(flags, "UnusualAmount").text = str(transfers.get("unusual_amount", False)).lower()
        ET.SubElement(flags, "FrequentTransfers").text = str(transfers.get("frequent_transfers", False)).lower()
        ET.SubElement(flags, "ManualReviewRequired").text = str(transfers.get("manual_review_required", False)).lower()

        # Escribir el archivo AML
        tree = ET.ElementTree(root)
        with open(file_path, "wb") as file:
            tree.write(file, encoding="utf-8", xml_declaration=True)

        return {"success": True, "file_path": file_path}
    except Exception as e:
        logger.error(f"Error al generar el archivo AMLTransactionReport: {str(e)}", exc_info=True)
        return {"error": "Error al generar el archivo AMLTransactionReport"}