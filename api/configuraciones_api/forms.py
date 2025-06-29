from django import forms
from api.configuraciones_api.models import ConfiguracionAPI

class ConfiguracionAPIForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionAPI
        fields = '__all__'
        widgets = {
            'entorno': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }