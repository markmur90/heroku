from django.apps import apps
from django.template.loader import get_template

def get_model(name: str):
    return apps.get_model('gpt4', name)

Transfer = get_model('Transfer')
LogTransferencia = get_model('LogTransferencia')


def load_template(name: str) -> str:
    """Return the raw template source using Django's loader."""
    template = get_template(name)
    return template.template.source


