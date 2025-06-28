import requests
import uuid

# URL del endpoint
url = "https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"

# Headers
headers = {
    "Authorization": "Bearer <ACCESS_TOKEN>",  # Reemplaza con tu token de acceso
    "idempotency-id": str(uuid.uuid4()),  # Genera un UUID único
    "otp": "4jv9xltr5",  # Reemplaza con tu OTP válido
    "Content-Type": "application/json"
}

# Cuerpo de la solicitud
data = {
    "purposeCode": "ABCD",
    "requestedExecutionDate": "2025-04-15",
    "debtor": {
        "debtorName": "John Doe",
        "debtorPostalAddress": {
            "country": "DE",
            "addressLine": {
                "streetAndHouseNumber": "Main Street 123",
                "zipCodeAndCity": "12345 Berlin"
            }
        }
    },
    "debtorAccount": {
        "iban": "DE89370400440532013000",
        "currency": "EUR"
    },
    "paymentIdentification": {
        "endToEndId": "E2E123456789",
        "instructionId": "INST123456789"
    },
    "instructedAmount": {
        "amount": 100.50,
        "currency": "EUR"
    },
    "creditorAgent": {
        "financialInstitutionId": "BANKDEFFXXX"
    },
    "creditor": {
        "creditorName": "Jane Smith",
        "creditorPostalAddress": {
            "country": "DE",
            "addressLine": {
                "streetAndHouseNumber": "Second Street 456",
                "zipCodeAndCity": "54321 Munich"
            }
        }
    },
    "creditorAccount": {
        "iban": "DE75512108001245126199",
        "currency": "EUR"
    },
    "remittanceInformationStructured": "Invoice 12345",
    "remittanceInformationUnstructured": "Payment for services"
}

# Enviar la solicitud
response = requests.post(url, headers=headers, json=data)

# Manejar la respuesta
if response.status_code == 201:
    print("Transacción creada exitosamente:", response.json())
else:
    print("Error al crear la transacción:", response.status_code, response.text)