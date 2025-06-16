# views.py
from django.shortcuts import render
from django.views import View
from django import forms
from django.http import HttpResponse
from lxml import etree
import requests

class SepaTransferForm(forms.Form):
    # Campos del deudor (deudor)
    debtor_name = forms.CharField(max_length=140, label="Nombre del Deudor")
    debtor_iban = forms.CharField(
        max_length=34,
        label="IBAN del Deudor",
        help_text="Formato: DE89370400440532013000"
    )
    
    # Campos del acreedor (creditor)
    creditor_name = forms.CharField(max_length=70, label="Nombre del Acreedor")
    creditor_iban = forms.CharField(
        max_length=34,
        label="IBAN del Acreedor",
        help_text="Formato: ES9121000418450200051332"
    )
    creditor_agent_id = forms.CharField(
        max_length=35,
        label="ID de la Institución Financiera (Acreedor)",
        help_text="Ejemplo: BANKDEFF"
    )
    
    # Monto y moneda
    amount = forms.DecimalField(
        label="Monto (EUR)",
        max_digits=10,
        decimal_places=2,
        min_value=0.01
    )
    requested_execution_date = forms.DateField(
        label="Fecha de Ejecución",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Formato: yyyy-MM-dd"
    )
    
    # OTP e Idempotencia (simulación)
    otp = forms.CharField(
        label="OTP",
        widget=forms.PasswordInput,
        help_text="Use 'PUSHTAN' para pushTAN"
    )
    idempotency_id = forms.CharField(
        label="ID de Idempotencia",
        max_length=36,
        help_text="UUID único para evitar duplicados"
    )

class SepaTransferView(View):
    template_name = "sepa_transfer_form.html"

    def get(self, request):
        form = SepaTransferForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SepaTransferForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        # Generar XML pain.001
        xml_data = self._generate_pain001(form.cleaned_data)
        
        # Enviar al banco (simulación)
        headers = {
            "idempotency-id": form.cleaned_data["idempotency_id"],
            "otp": form.cleaned_data["otp"],
            "Content-Type": "application/xml"
        }
        response = requests.post(
            "https://simulator-api.db.com/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer",
            data=xml_data,
            headers=headers
        )
        
        # Procesar respuesta pain.002
        if response.status_code == 201:
            return HttpResponse("Transferencia exitosa. Respuesta XML:\n" + response.text)
        else:
            return HttpResponse(f"Error: {response.status_code}\n{response.text}")

    def _generate_pain001(self, data):
        root = etree.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
        cstmr_cdt_trf_initn = etree.SubElement(root, "CstmrCdtTrfInitn")
        
        # Cabecera (simplificada)
        grp_hdr = etree.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
        etree.SubElement(grp_hdr, "MsgId").text = data["idempotency_id"]
        etree.SubElement(grp_hdr, "CreDtTm").text = "2023-10-01T12:00:00"
        
        # Información de pago
        pmt_inf = etree.SubElement(cstmr_cdt_trf_initn, "PmtInf")
        etree.SubElement(pmt_inf, "ReqdExctnDt").text = data["requested_execution_date"].strftime("%Y-%m-%d")
        
        # Deudor
        dbtr = etree.SubElement(pmt_inf, "Dbtr")
        etree.SubElement(dbtr, "Nm").text = data["debtor_name"]
        dbtr_acct = etree.SubElement(pmt_inf, "DbtrAcct")
        etree.SubElement(dbtr_acct, "Id", {"IBAN": data["debtor_iban"]})
        
        # Acreedor
        cdtr = etree.SubElement(pmt_inf, "Cdtr")
        etree.SubElement(cdtr, "Nm").text = data["creditor_name"]
        cdtr_acct = etree.SubElement(pmt_inf, "CdtrAcct")
        etree.SubElement(cdtr_acct, "Id", {"IBAN": data["creditor_iban"]})
        
        # Monto
        amt = etree.SubElement(pmt_inf, "Amt")
        etree.SubElement(amt, "InstdAmt", Ccy="EUR").text = str(data["amount"])
        
        return etree.tostring(root, pretty_print=True, encoding="utf-8")


# views.py
class CheckStatusForm(forms.Form):
    payment_id = forms.CharField(
        label="ID de Pago",
        max_length=36,
        help_text="UUID de la transacción"
    )

class CheckStatusView(View):
    template_name = "check_status_form.html"

    def get(self, request):
        form = CheckStatusForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CheckStatusForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        # Simular solicitud al banco
        headers = {"Content-Type": "application/xml"}
        response = requests.get(
            f"https://simulator-api.db.com/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{form.cleaned_data['payment_id']}/status",
            headers=headers
        )
        
        # Procesar respuesta pain.002
        return HttpResponse(f"Estado de la transacción:\n{response.text}")


