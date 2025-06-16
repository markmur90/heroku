import uuid
from datetime import datetime
import pytz
from django import forms
from api.sct.models import (
    CreditorAgent,
    SepaCreditTransferRequest,
    Address,
    Debtor,
    Account,
    PaymentIdentification,
    InstructedAmount,
    Creditor,
    SepaCreditTransfer,
    
)


class SepaCreditTransferRequestForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransferRequest
        fields = '__all__'
        widgets = {
            'transaction_status': forms.Select(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de DateInput a TextInput
            
            'debtor_name': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_street_and_house_number': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_zip_code_and_city': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_country': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_iban': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_bic': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_currency': forms.Select(attrs={'class': 'form-control'}),

            'payment_identification_end_to_end_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_identification_instruction_id': forms.TextInput(attrs={'class': 'form-control'}),
            
            'instructed_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'instructed_currency': forms.Select(attrs={'class': 'form-control'}),  # Corregido de TextInput a Select
            
            'creditor_name': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_street_and_house_number': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_zip_code_and_city': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_country': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_iban': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_bic': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_currency': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent_financial_institution_id': forms.Select(attrs={'class': 'form-control'}),

            'remittance_information_structured': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de Textarea a TextInput
            'remittance_information_unstructured': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de Textarea a TextInput

         
            'requested_execution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'idempotency_key': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_id': forms.TextInput(attrs={'class': 'form-control'}),
            'auth_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = '__all__'
        widgets = {
            'country': forms.TextInput(attrs={'pattern': '[A-Z]{2}', 'class': 'form-control'}),
            'street_and_house_number': forms.TextInput(attrs={'maxlength': 70, 'class': 'form-control'}),
            'zip_code_and_city': forms.TextInput(attrs={'maxlength': 70, 'class': 'form-control'}),
        }

class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = ['debtor_name', 'debtor_postal_address']
        widgets = {
            'debtor_name': forms.TextInput(attrs={'maxlength': 100, 'class': 'form-control'}),
            'debtor_postal_address': forms.Select(attrs={'class': 'form-control'}),
        }

class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        fields = ['creditor_name', 'creditor_postal_address']
        widgets = {
            'creditor_name': forms.TextInput(attrs={'maxlength': 100, 'class': 'form-control'}),
            'creditor_postal_address': forms.Select(attrs={'class': 'form-control'}),
        }

class CreditorAgentForm(forms.ModelForm):
    class Meta:
        model = CreditorAgent
        fields = ['financial_institution_id']
        widgets = {
            'financial_institution_id': forms.TextInput(attrs={'maxlength': 35, 'class': 'form-control'}),
        }
        
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = '__all__'
        widgets = {
            'iban': forms.TextInput(attrs={'pattern': '[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}', 'maxlength': 34, 'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'pattern': '[A-Z]{3}', 'maxlength': 3, 'class': 'form-control'}),
        }

class PaymentIdentificationForm(forms.ModelForm):
    class Meta:
        model = PaymentIdentification
        fields = '__all__'
        widgets = {
            'end_to_end_id': forms.TextInput(attrs={'pattern': '[a-zA-Z0-9.-]{1,36}'}),
            'instruction_id': forms.TextInput(attrs={'pattern': '[a-zA-Z0-9.-]{1,36}'})
        }

class InstructedAmountForm(forms.ModelForm):
    class Meta:
        model = InstructedAmount
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'pattern': '[A-Z]{3}', 'maxlength': 3, 'class': 'form-control'}),
        }

from django.forms import ModelChoiceField
from django.urls import reverse_lazy

class SepaCreditTransferForm(forms.ModelForm):
    debtor = ModelChoiceField(
        queryset=Debtor.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Deudor",
        help_text="Seleccione un deudor existente o cree uno nuevo."
    )
    debtor_account = ModelChoiceField(
        queryset=Account.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Cuenta del Deudor",
        help_text="Seleccione una cuenta existente o cree una nueva."
    )
    creditor = ModelChoiceField(
        queryset=Creditor.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Acreedor",
        help_text="Seleccione un acreedor existente o cree uno nuevo."
    )
    creditor_account = ModelChoiceField(
        queryset=Account.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Cuenta del Acreedor",
        help_text="Seleccione una cuenta existente o cree una nueva."
    )
    creditor_agent = ModelChoiceField(
        queryset=CreditorAgent.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Agente del Acreedor",
        help_text="Seleccione un agente existente o cree uno nuevo."
    )
    instructed_amount = ModelChoiceField(
        queryset=InstructedAmount.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Monto Instruido",
        help_text="Seleccione un monto existente o cree uno nuevo."
    )

    class Meta:
        model = SepaCreditTransfer
        exclude = ['payment_id', 'auth_id', 'transaction_status', 'created_at', 'updated_at', 'end_to_end_id', 'instruction_id', 'requested_execution_date']
        widgets = {
            'purpose_code': forms.TextInput(attrs={
                'pattern': '.{4}',
                'class': 'form-control',
                'placeholder': 'Ingrese un código de 4 caracteres'
            }),
            'requested_execution_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Seleccione una fecha'
            }),
            'remittance_information_structured': forms.TextInput(attrs={
                'maxlength': 60,
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'Ingrese información estructurada (máx. 60 caracteres)'
            }),
            'remittance_information_unstructured': forms.TextInput(attrs={
                'maxlength': 60,
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'Ingrese información no estructurada (máx. 60 caracteres)'
            })
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Establecer la fecha y hora actual de Frankfurt
        frankfurt_tz = pytz.timezone('Europe/Berlin')
        instance.requested_execution_date = datetime.now(frankfurt_tz)

        # # Crear o asociar automáticamente un PaymentIdentification
        # if not instance.payment_identification:
        #     instance.payment_identification, _ = PaymentIdentification.objects.get_or_create(
        #         end_to_end_id=uuid.uuid4().hex[:36],
        #         instruction_id=uuid.uuid4().hex[:36]
        #     )

        if commit:
            instance.save()
        return instance