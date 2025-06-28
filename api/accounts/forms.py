from django import forms
from api.accounts.models import Account

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'status', 'balance', 'currency', 'iban', 'type', 'is_main']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'is_main': forms.Select(attrs={'class': 'form-control'}),
        }
 
    def clean_balance(self):
        balance = self.cleaned_data.get('balance')
        if balance is not None and balance < 0:
            raise forms.ValidationError("Balance cannot be negative.")
        return balance
        