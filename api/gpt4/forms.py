from datetime import datetime
from django import forms
import pytz
from api.gpt4.models import ClaveGenerada, ClientID, Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent, Kid, Transfer

class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_id': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_street': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_city': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_phone_number': forms.TextInput(attrs={'class':'form-control','placeholder':'+4915…'}),
        }

class DebtorAccountForm(forms.ModelForm):
    class Meta:
        model = DebtorAccount
        fields = '__all__'
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_street': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_city': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorAccountForm(forms.ModelForm):
    class Meta:
        model = CreditorAccount
        fields = '__all__'
        widgets = {
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorAgentForm(forms.ModelForm):
    class Meta:
        model = CreditorAgent
        fields = '__all__'
        widgets = {
            'bic': forms.TextInput(attrs={'class': 'form-control'}),
            'financial_institution_id': forms.TextInput(attrs={'class': 'form-control'}),
            'other_information': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = [
            'debtor', 'debtor_account', 'creditor', 'creditor_account',
            'creditor_agent', 'instructed_amount', 'currency',
            'purpose_code', 'requested_execution_date',
            'remittance_information_unstructured'
        ]
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent': forms.Select(attrs={'class': 'form-control'}),
            'instructed_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),
            'requested_execution_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d')
            }),
            'remittance_information_unstructured': forms.TextInput(attrs={
                'maxlength': 60,
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'Ingrese información no estructurada (máx. 60 caracteres)'
            }),
        }


class SendTransferForm(forms.ModelForm):
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
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Introduce OTP manual de 6 a 8 caracteres'})
    )
    OTP_METHOD_CHOICES = [
    ('MTAN', 'SMS (MTAN)'),
    ('PHOTOTAN', 'PhotoTAN'),
    ('PUSHTAN', 'PushTAN'),
    ]
    otp_method = forms.ChoiceField(
    choices=OTP_METHOD_CHOICES,
    widget=forms.RadioSelect,
    label='Método de entrega OTP',
    required=False
    )
    
    class Meta:
        model = Transfer
        fields = [
            'client', 'kid'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'kid': forms.Select(attrs={'class': 'form-control'}),   
        }
             
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
        
        if cleaned_data.get('obtain_otp') and not cleaned_data.get('otp_method'):
            raise forms.ValidationError('Si obtienes OTP automáticamente, debes elegir un método.')

        return cleaned_data

class ScaForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('APPROVE','Aprobar'),('CANCEL','Cancelar')],
        widget=forms.Select(attrs={'class':'form-select'})
    )
    otp = forms.CharField(
        label='Código OTP',
        widget=forms.TextInput(attrs={'class':'form-control','maxlength':8})
    )
    
class ClientIDForm(forms.ModelForm):
    class Meta:
        model = ClientID
        fields = ['codigo', 'clientId']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'clientId': forms.TextInput(attrs={'class': 'form-control'}),
        }

class KidForm(forms.ModelForm):
    class Meta:
        model = Kid
        fields = ['codigo', 'kid']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'kid': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ClaveGeneradaForm(forms.ModelForm):
    class Meta:
        model = ClaveGenerada
        fields = [
            'usuario',
            'estado',
            'kid',
            'path_privada',
            'path_publica',
            'path_jwks',
            'clave_privada',
            'clave_publica',
            'jwks',
            'archivo_privado',
            'archivo_publico',
            'archivo_jwks',
            'mensaje_error',
        ]


class SendTransferSimulatorForm(forms.Form):
    otp = forms.CharField(
        label='Código OTP',
        min_length=6,
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )