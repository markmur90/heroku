import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from api.sct.models import SepaCreditTransferRequest
logger = logging.getLogger("bank_services")


def generate_sepa_xml2(transfers: SepaCreditTransferRequest) -> str:
    """
    Genera un XML SEPA (ISO 20022) para la transferencia.
    """
    # Crear el documento XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")
 
    # Información del grupo de pagos
    GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
    ET.SubElement(GrpHdr, "MsgId").text = str(transfers.idempotency_key)
    ET.SubElement(GrpHdr, "CreDtTm").text = datetime.utcnow().isoformat()
    ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
    ET.SubElement(GrpHdr, "CtrlSum").text = str(transfers.instructed_amount)
    InitgPty = ET.SubElement(GrpHdr, "InitgPty")
    ET.SubElement(InitgPty, "Nm").text = transfers.debtor_name

    # Información de la transacción
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    ET.SubElement(PmtInf, "PmtInfId").text = str(transfers.payment_id)
    ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transferencia
    ET.SubElement(PmtInf, "BtchBookg").text = "false"
    ET.SubElement(PmtInf, "NbOfTxs").text = "1"
    ET.SubElement(PmtInf, "CtrlSum").text = str(transfers.instructed_amount)

    PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
    SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
    ET.SubElement(SvcLvl, "Cd").text = "SEPA"

    ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
    ReqdExctnDt.text = transfers.requested_execution_date.strftime("%Y-%m-%d")

    # Datos del ordenante
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    ET.SubElement(Dbtr, "Nm").text = transfers.debtor_name

    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    Id = ET.SubElement(DbtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = transfers.debtor_account_iban

    DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
    FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = transfers.debtor_account_bic

    # Datos del beneficiario
    CdtTrfTxInf = ET.SubElement(PmtInf, "CdtTrfTxInf")
    PmtId = ET.SubElement(CdtTrfTxInf, "PmtId")
    ET.SubElement(PmtId, "EndToEndId").text = str(transfers.payment_identification_end_to_end_id)

    Amt = ET.SubElement(CdtTrfTxInf, "Amt")
    ET.SubElement(Amt, "InstdAmt", Ccy=transfers.instructed_currency).text = str(transfers.instructed_amount)

    CdtrAgt = ET.SubElement(CdtTrfTxInf, "CdtrAgt")
    FinInstnId = ET.SubElement(CdtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = transfers.creditor_account_bic

    Cdtr = ET.SubElement(CdtTrfTxInf, "Cdtr")
    ET.SubElement(Cdtr, "Nm").text = transfers.creditor_name

    CdtrAcct = ET.SubElement(CdtTrfTxInf, "CdtrAcct")
    Id = ET.SubElement(CdtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = transfers.creditor_account_iban

    RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
    ET.SubElement(RmtInf, "Ustrd").text = transfers.remittance_information_unstructured

    # Generar el XML
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return xml_string
    