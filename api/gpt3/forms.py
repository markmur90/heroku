from datetime import datetime
from django import forms
import pytz
from api.gpt3.models import *


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = '__all__'
        widgets = {
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'street_and_house_number': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code_and_city': forms.TextInput(attrs={'class': 'form-control'})
        }


class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = '__all__'
        widgets = {
            'debtor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_id': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address': forms.Select(attrs={'class': 'form-control'})
        }


class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        fields = '__all__'
        widgets = {
            'creditor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address': forms.Select(attrs={'class': 'form-control'})
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = '__all__'
        widgets = {
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'})
        }
        

class FinancialInstitutionForm(forms.ModelForm):
    class Meta:
        model = FinancialInstitution
        fields = '__all__'
        widgets = {
            'financial_institution_id': forms.TextInput(attrs={'class': 'form-control'})
        }


class PaymentIdentificationForm(forms.ModelForm):
    class Meta:
        model = PaymentIdentification
        fields = '__all__'
        widgets = {
            'end_to_end_id': forms.TextInput(attrs={'class': 'form-control'}),
            'instruction_id': forms.TextInput(attrs={'class': 'form-control'})
        }


class InstructedAmountForm(forms.ModelForm):
    class Meta:
        model = InstructedAmount
        fields = '__all__'
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'})
        }


class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransfer
        fields = '__all__'
        exclude = ['payment_id', 'auth_id', 'transaction_status', 'payment_identification']
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent': forms.Select(attrs={'class': 'form-control'}),
            'instructed_amount': forms.Select(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),
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


class GroupHeaderForm(forms.ModelForm):
    class Meta:
        model = GroupHeader
        fields = '__all__'
        widgets = {
            'message_id': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_transactions': forms.NumberInput(attrs={'class': 'form-control'}),
            'control_sum': forms.NumberInput(attrs={'class': 'form-control'}),
            'initiating_party_name': forms.TextInput(attrs={'class': 'form-control'}),
            'create_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
        }


class BulkTransferForm(forms.ModelForm):
    class Meta:
        model = BulkTransfer
        fields = ['payment_id', 'group_header', 'transaction_status']
        widgets = {
            'payment_id': forms.TextInput(attrs={'class': 'form-control'}),
            'group_header': forms.Select(attrs={'class': 'form-control'}),
            'transaction_status': forms.Select(attrs={'class': 'form-control'})
        }


class PaymentInformationForm(forms.ModelForm):
    class Meta:
        model = PaymentInformation
        fields = '__all__'
        widgets = {
            'payment_information_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_booking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'number_of_transactions': forms.NumberInput(attrs={'class': 'form-control'}),
            'control_sum': forms.NumberInput(attrs={'class': 'form-control'}),
            'requested_execution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account': forms.Select(attrs={'class': 'form-control'}),
            'debtor_agent': forms.Select(attrs={'class': 'form-control'}),
            'charge_bearer': forms.TextInput(attrs={'class': 'form-control'})
        }


class CreditTransfersDetailsForm(forms.ModelForm):
    class Meta:
        model = CreditTransfersDetails
        fields = '__all__'
        widgets = {
            'payment_information': forms.Select(attrs={'class': 'form-control'}),
            'payment_identification': forms.Select(attrs={'class': 'form-control'}),
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account': forms.Select(attrs={'class': 'form-control'}),
            'instructed_amount': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent': forms.Select(attrs={'class': 'form-control'}),
            'remittance_information_unstructured': forms.TextInput(attrs={'class': 'form-control'})
        }


class SendTransferForm(forms.Form):
    obtain_token = forms.BooleanField(
        required=False,
        label='Obtener nuevo TOKEN',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    manual_token = forms.CharField(
        required=False,
        label='TOKEN manual',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Introduce TOKEN manual si aplica'})
    )
    obtain_otp = forms.BooleanField(
        required=False,
        label='Obtener nuevo OTP',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    manual_otp = forms.CharField(
        required=False,
        label='OTP manual',
        min_length=6,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Introduce OTP manual de 6 a 8 caracteres'})
    )

    def clean(self):
        cleaned_data = super().clean()
        obtain_token = cleaned_data.get('obtain_token')
        manual_token = cleaned_data.get('manual_token')
        obtain_otp = cleaned_data.get('obtain_otp')
        manual_otp = cleaned_data.get('manual_otp')

        if not obtain_token and not manual_token:
            raise forms.ValidationError('Debes seleccionar obtener TOKEN o proporcionar uno manualmente.')

        if not obtain_otp and not manual_otp:
            raise forms.ValidationError('Debes seleccionar obtener OTP o proporcionar uno manualmente.')

        return cleaned_data