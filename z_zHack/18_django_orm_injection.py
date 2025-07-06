import requests
import json
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from simulador_banco.banco.models import Transfer, Debtor, Creditor, DebtorAccount, CreditorAgent

# Datos de transferencia válidos desde modelo Django
def fake_django_orm_transaction():
    # Simulamos la estructura completa de un objeto Transfer desde Django ORM
    transfer_data = {
        "payment_id": "550e8400-e29b-41d4-a716-446655440000",
        "debtor_account_id": 112233,
        "creditor_account_id": 445566,
        "instructed_amount": 49000.00,
        "currency": "EUR",
        "purpose_code": "GDSV",
        "requested_execution_date": datetime.today().date(),
        "remittance_information_unstructured": "Aprobado por gerencia",
        "status": "ACSC",
        "auth_id": "USR-ADM-001"
    }

    # Aquí creamos un objeto Transfer con los campos exactos del ORM
    # Y fingimos que somos una transferencia desde el sistema Django
    transfer = Transfer(**{
        'payment_id': "550e8400-e29b-41d4-a716-446655440000",
        'debtor': Debtor.objects.get(name="Anna Meyer"),
        'creditor': Creditor.objects.get(name="Tom Winter"),
        'debtor_account': DebtorAccount.objects.get(iban="DE0050000100200044824",
                                                    currency="EUR"),
        'creditor_account': CreditorAccount.objects.get(iban="DE00500700100200044874",
                                                       currency="EUR")
    })

    transfer.creditor_agent = CreditorAgent.objects.get(financial_institution_id="CAIXESBB")
    transfer.save()

    print("[+] Django ORM inyectado. El sistema aceptó la transferencia como interna.")
    return transfer

# === Correr desde entorno Django (lo necesitamos para importar y crear objetos desde modelo ===

try:
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.db import models

    get_wsgi_application()  # Cargamos Django para poder usar modelos

    transaction = fake_django_orm_transaction()
    print("[+] Transacción Django ORM completada. Status:", transaction.status)

except Exception as e:
    print("[-] No estamos desde el entorno de Django.")
    print("No podemos ejecutar ORM directo ni crear Transfer() dentro del modelo.")
    print("Error de entorno:", e)