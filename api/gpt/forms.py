from django import forms
from datetime import datetime
import pytz
from .models import (
    SepaCreditTransfer, Account, Amount,
    FinancialInstitution, PostalAddress, PaymentIdentification, Debtor, Creditor
)


class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'debtor', 'debtor_account', 'creditor', 'creditor_account',
            'creditor_agent', 'instructed_amount', 'purpose_code',
            'requested_execution_date', 'remittance_information_structured',
            'remittance_information_unstructured'
        ]
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent': forms.Select(attrs={'class': 'form-control'}),
            'instructed_amount': forms.Select(attrs={'class': 'form-control'}),
            'requested_execution_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d')
            }),
            'purpose_code': forms.TextInput(attrs={
                'pattern': '.{4}',
                'class': 'form-control',
                'placeholder': 'Ingrese un código de 4 caracteres'
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
            }),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['iban', 'currency']
        widgets = {
            'iban': forms.TextInput(attrs={'pattern': '[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}', 'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'pattern': '[A-Z]{3}', 'class': 'form-control'}),
        }


class AmountForm(forms.ModelForm):
    class Meta:
        model = Amount
        fields = ['amount', 'currency']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'pattern': '[A-Z]{3}', 'class': 'form-control'}),
        }


class FinancialInstitutionForm(forms.ModelForm):
    class Meta:
        model = FinancialInstitution
        fields = ['financial_institution_id']
        widgets = {
            'financial_institution_id': forms.TextInput(attrs={'maxlength': 36, 'class': 'form-control'}),
        }


class PostalAddressForm(forms.ModelForm):
    class Meta:
        model = PostalAddress
        fields = ['country', 'zip_code_and_city', 'street_and_house_number']
        widgets = {
            'country': forms.TextInput(attrs={'pattern': '[A-Z]{2}', 'class': 'form-control'}),
            'zip_code_and_city': forms.TextInput(attrs={'maxlength': 70, 'class': 'form-control'}),
            'street_and_house_number': forms.TextInput(attrs={'maxlength': 70, 'class': 'form-control'}),
        }


class PaymentIdentificationForm(forms.ModelForm):
    class Meta:
        model = PaymentIdentification
        fields = ['end_to_end_id', 'instruction_id']
        widgets = {
            'end_to_end_id': forms.TextInput(attrs={'pattern': '[a-zA-Z0-9.-]{1,35}', 'class': 'form-control'}),
            'instruction_id': forms.TextInput(attrs={'pattern': '[a-zA-Z0-9.-]{1,35}', 'class': 'form-control'}),
        }


class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = ['debtor_name', 'postal_address']
        widgets = {
            'debtor_name': forms.TextInput(attrs={'maxlength': 100, 'class': 'form-control'}),
            'postal_address': forms.Select(attrs={'class': 'form-control'}),
        }


class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        fields = ['creditor_name', 'postal_address']
        widgets = {
            'creditor_name': forms.TextInput(attrs={'maxlength': 100, 'class': 'form-control'}),
            'postal_address': forms.Select(attrs={'class': 'form-control'}),
        }
