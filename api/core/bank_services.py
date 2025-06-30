import requests, uuid
from config import settings
from .auth_services import get_simulator_token

def real_transfer(user, pwd, source, dest, amount, currency, totp_code):
    # 1) Autenticación
    token = get_simulator_token(user, pwd)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payment_id = str(uuid.uuid4())

    # 2) Desafío OTP
    challenge_resp = requests.post(
        settings.CHALLENGE_URL,
        json={"payment_id": payment_id, "amount": amount, "currency": currency, "source": source, "destination": dest},
        headers=headers
    )
    challenge_resp.raise_for_status()
    otp = challenge_resp.json()["otp"]

    # 3) Confirmación con OTP + TOTP
    confirm_resp = requests.post(
        settings.TRANSFER_URL,
        json={"payment_id": payment_id, "otp": otp, "totp": totp_code},
        headers=headers
    )
    confirm_resp.raise_for_status()
    return confirm_resp.json()
