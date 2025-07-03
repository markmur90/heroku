
from api.gpt4.conexion.conexion_banco import make_request


def enviar_transferencia_simulador(payment_id: str, token: str, otp: str) -> tuple[bool, str]:
    """
    Envía una transferencia real al simulador bancario.
    Requiere token de autorización y OTP válido generado previamente.
    """
    try:
        response = make_request(
            method="POST",
            path="/api/send-transfer",
            token=token,
            payload={
                "payment_id": payment_id,
                "otp": otp
            }
        )
        if response.status_code == 200:
            return True, "Transferencia completada"
        else:
            data = response.json()
            return False, data.get("error", "Error desconocido en simulador")

    except Exception as e:
        return False, f"Excepción al enviar transferencia: {str(e)}"
