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
                'placeholder': 'Ingrese información no estructurada (máx. 60 caracteres)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('instructed_amount')
        exec_date = cleaned_data.get('requested_execution_date')
        debtor = cleaned_data.get('debtor')
        debtor_account = cleaned_data.get('debtor_account')
        creditor = cleaned_data.get('creditor')
        creditor_account = cleaned_data.get('creditor_account')
        if amount is not None and amount <= 0:
            self.add_error('instructed_amount', 'El monto debe ser positivo.')
        if exec_date and exec_date < datetime.now(pytz.timezone('Europe/Berlin')).date():
            self.add_error('requested_execution_date', 'La fecha de ejecución no puede ser pasada.')
        if debtor and debtor_account and debtor_account.debtor != debtor:
            self.add_error('debtor_account', 'La cuenta seleccionada no pertenece al deudor.')
        if creditor and creditor_account and creditor_account.creditor != creditor:
            self.add_error('creditor_account', 'La cuenta seleccionada no pertenece al acreedor.')
        return cleaned_data

class SendTransferForm(forms.ModelForm):
    obtain_token = forms.BooleanField(
        required=False,
        label='Obtener nuevo TOKEN',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    manual_token = forms.CharField(
        required=False,
        label='TOKEN manual',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce TOKEN manual si aplica'
        })
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
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Introduce OTP de 6 dígitos'
        })
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
        fields = ['client', 'kid']  # Campos relacionados con el cliente API, si los hubiera
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'kid': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.context_mode = kwargs.pop('context_mode', 'full')  # 'simple_otp' para solo pedir OTP
        super().__init__(*args, **kwargs)
        if self.context_mode == 'simple_otp':
            # 🔧 En modo simple_otp ocultamos campos de token y método OTP, dejando solo el campo OTP manual
            for field in ['obtain_token', 'manual_token', 'obtain_otp', 'otp_method', 'client', 'kid']:
                self.fields.pop(field, None)

    def clean(self):
        cleaned_data = super().clean()
        if self.context_mode == 'simple_otp':
            # En modo simplificado, solo requerimos que el OTP manual esté presente
            manual_otp = cleaned_data.get('manual_otp')
            if not manual_otp:
                raise forms.ValidationError('Debes ingresar un código OTP.')
            return cleaned_data

        # Validación en modo completo (no suele usarse tras refactor):
        obtain_token = cleaned_data.get('obtain_token')
        manual_token = cleaned_data.get('manual_token')
        obtain_otp = cleaned_data.get('obtain_otp')
        manual_otp = cleaned_data.get('manual_otp')
        otp_method = cleaned_data.get('otp_method')

        # if not obtain_token and not manual_token:
            # raise forms.ValidationError('Selecciona obtener TOKEN o proporciona uno manual.')

        if not obtain_otp and not manual_otp:
            raise forms.ValidationError('Selecciona obtener OTP o proporciona uno manual.')

        if obtain_otp and not otp_method:
            raise forms.ValidationError('Seleccionaste OTP automático pero no elegiste método.')

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

