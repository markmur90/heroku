from django.apps import apps

def get_model(name: str):
    return apps.get_model('gpt4', name)

Transfer = get_model('Transfer')
LogTransferencia = get_model('LogTransferencia')


