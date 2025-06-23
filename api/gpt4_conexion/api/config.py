# api/config.py
from django.conf import settings

BANK_API_TOKEN = settings.BANK_API_TOKEN
TRANSFER_ENDPOINT = f"/api/transferencia"
HEADERS = {
    'Authorization': f"Bearer {BANK_API_TOKEN}",
    'Content-Type': 'application/json'
}