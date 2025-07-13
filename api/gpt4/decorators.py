import logging
from datetime import datetime
from functools import wraps
from django.http import JsonResponse
from django.utils.timezone import now
from api.gpt4.models import Transfer
from api.gpt4.utils import registrar_log

logger = logging.getLogger(__name__)

def registro_transferencia(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        payment_id = kwargs.get("payment_id") or request.GET.get("payment_id")
        if not payment_id:
            return JsonResponse({"error": "payment_id no proporcionado"}, status=400)

        try:
            transfer = Transfer.objects.get(payment_id=payment_id)
        except Transfer.DoesNotExist:
            return JsonResponse({"error": "Transferencia no encontrada"}, status=404)

        registrar_log(payment_id, "Inicio del proceso", extra_info={"usuario": request.user.username})
        logger.info(f"[{payment_id}] Inicio proceso por {request.user.username}")

        response = view_func(request, transfer=transfer, *args, **kwargs)

        transfer.requested_execution_date = now()
        transfer.auth_id = request.user.username
        transfer.save()

        registrar_log(payment_id, "Fin del proceso", extra_info={"estado": transfer.status})
        logger.info(f"[{payment_id}] Proceso terminado. Estado: {transfer.status}")

        return response
    return wrapper
