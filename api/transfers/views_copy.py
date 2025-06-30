from rest_framework import generics
from api.transfers.models import SEPA2, Transfer
from api.transfers.serializers import SEPA2Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from rest_framework.exceptions import APIException
import logging
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from api.transfers.forms import SEPA2Form
from django.contrib import messages
from api.core.services import generate_sepa_xml
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
import os
from django.template.loader import render_to_string

logger = logging.getLogger("bank_services")



class BaseTransferView(CreateView):
    permission_classes = [AllowAny]

    def _get_existing_record(self, model, key_value, key_field):
        """Helper to retrieve an existing record by a unique key."""
        filter_kwargs = {key_field: key_value}
        return model.objects.filter(**filter_kwargs).first()

    def _error_response(self, message, status_code):
        return Response({"error": message}, status=status_code)

    def _success_response(self, data, status_code):
        return Response(data, status_code)
    
    def _generate_success_template(self, transfer, sepa_xml):
        """Genera una plantilla de respuesta exitosa para una transferencia."""
        return {
            "transfer": {
                "id": transfer.id,
                "source_account": transfer.source_account,
                "destination_account": transfer.destination_account,
                "amount": transfer.amount,
                "currency": transfer.currency,
                "status": transfer.status,
            },
            "sepa_xml": sepa_xml,
        }

    def _generate_error_template(self, error_message):
        """Genera una plantilla de respuesta de error."""
        return {
            "error": {
                "message": error_message,
                "code": "TRANSFER_ERROR",
            }
        }

class TransferCOPYCreateView(BaseTransferView):
    @swagger_auto_schema(operation_description="Create a transfer", request_body=SEPA2Serializer)
    def post(self, request):
        IDEMPOTENCY_HEADER = "Idempotency-Key"
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return self._error_response(f"{IDEMPOTENCY_HEADER} header is required", status.HTTP_400_BAD_REQUEST)

        existing_transfer = self._get_existing_record(Transfer, idempotency_key, "idempotency_key")
        if existing_transfer:
            return self._success_response(
                {"message": "Duplicate transfer", "transfer_id": existing_transfer.id}, status.HTTP_200_OK
            )

        serializer = SEPA2Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transfer_data = serializer.validated_data
        bank = request.data.get("bank")

        try:
            response = self.process_bank_transfer(bank, transfer_data, idempotency_key)
            if "error" in response:
                logger.warning(f"Error en la transferencia: {response['error']}")
                return self._error_response(self._generate_error_template(response['error']), status.HTTP_400_BAD_REQUEST)

            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            # Generar SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transfer)
                return self._success_response(
                    self._generate_success_template(transfer, sepa_xml), status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                return self._error_response(self._generate_error_template("Error generando SEPA XML"), status.HTTP_500_INTERNAL_SERVER_ERROR)

        except APIException as e:
            logger.error(f"Error en la transferencia: {str(e)}")
            return self._error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            raise APIException("Error inesperado en la transferencia bancaria.")

    def process_bank_transfer(self, bank, transfer_data, idempotency_key):
        transfer_functions = {
            "memo": memo_bank_transfer,
            "deutsche": deutsche_bank_transfer,
        }
        if bank not in transfer_functions:
            raise APIException("Invalid bank selection")

        try:
            return transfer_functions[bank](
                transfer_data["source_account"], transfer_data["destination_account"],
                transfer_data["amount"], transfer_data["currency"], idempotency_key
            )
        except Exception as e:
            logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
            raise APIException("Error procesando la transferencia bancaria.")
        
    def get_html_form_template(self):
        """Genera una plantilla HTML para ingresar datos de transferencia desde un archivo."""
        template_path = os.path.join("api/transfers/transfer_form.html")
        return render_to_string(template_path)

class SepaTransferCOPYCreateView(BaseTransferView):
    model = SEPA2  # Define el modelo asociado
    fields = "__all__"  # Especifica los campos del modelo que se usarán en el formulario
    template_name = "api/transfers/transfer_form.html"  # Define el nombre de la plantilla
    @swagger_auto_schema(operation_description="Create a SEPA transfer", request_body=SEPA2Serializer)
    def post(self, request):
        IDEMPOTENCY_HEADER = "Idempotency-Key"
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return self._error_response(f"{IDEMPOTENCY_HEADER} header is required", status.HTTP_400_BAD_REQUEST)

        existing_transaction = self._get_existing_record(SEPA2, idempotency_key, "transaction_id")
        if existing_transaction:
            return self._success_response(
                {"message": "Duplicate SEPA transfer", "transaction_id": existing_transaction.id}, status.HTTP_200_OK
            )

        serializer = SEPA2Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transaction = serializer.save()
        try:
            sepa_xml = generate_sepa_xml(transaction)
            return self._success_response(
                {"sepa_xml": sepa_xml, "transaction": serializer.data}, status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.critical(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            raise APIException("Unexpected error during SEPA transfer.")

    def get_html_form_template(self):
        """Genera una plantilla HTML para ingresar datos de transferencia desde un archivo."""
        template_path = os.path.join("api/extras", "api/transfers/transfer_form.html")
        return render_to_string(template_path)

class TransferCOPYListView(ListView):
    model = SEPA2
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"

class TransferCOPY2CreateView(BaseTransferView, CreateView):
    model = SEPA2
    form_class = SEPA2Form
    template_name = "api/transfers/transfer_form.html"

class TransferCOPY2UpdateView(BaseTransferView, UpdateView):
    model = SEPA2
    form_class = SEPA2Form
    template_name = "api/transfers/transfer_form.html"

class TransferCOPY2DeleteView(DeleteView):
    model = SEPA2
    template_name = "api/transfers/transfer_confirm_delete.html"
    success_url = "/transfers/"

