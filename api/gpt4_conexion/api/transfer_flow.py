# transfer_flow.py
from django.views import View
from django.http import JsonResponse
from .config import HEADERS, TRANSFER_ENDPOINT
from bank_connector import BankConnector
from api.gpt4.utils import generar_xml_pain001, registrar_log

class TransferView(View):
    connector = BankConnector()

    def post(self, request):
        data = request.json()
        pid = data.get('payment_id')
        xml = generar_xml_pain001(data)
        registrar_log(pid, tipo_log="TRANSFER_INIT")
        try:
            resp = self.connector.send(TRANSFER_ENDPOINT, json={'xml': xml})
            registrar_log(pid, tipo_log="TRANSFER_SUCCESS", extra_info=str(resp))
            return JsonResponse({'status': 'ok', **resp})
        except Exception as e:
            registrar_log(pid, tipo_log="TRANSFER_ERROR", extra_info=str(e))
            return JsonResponse({'status': 'error', 'message': 'Error interno'}, status=500)