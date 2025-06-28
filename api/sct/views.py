# Django imports
from config import settings
from django.http import FileResponse, HttpResponseNotFound, JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

# DRF imports
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

# Python standard library imports
import os
import logging
from uuid import uuid4
from datetime import date, datetime

# Local app imports
from api.sct.generate_aml import generate_aml_transaction_report
from api.sct.models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse, 
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from api.sct.process_bank import process_bank_transfer, process_bank_transfer_json
from api.sct.process_bank_json_xml_aml import process_bank_transfer_json_xml_aml, process_bank_transfer_jsonn
from api.sct.serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer, 
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)
from api.sct.forms import SepaCreditTransferRequestForm, AddressForm
from api.sct.generate_xml import generate_sepa_xml
from api.sct.generate_xml2 import generate_sepa_xml2
from api.sct.generate_xml3 import generate_sepa_xml3
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.process_transfer import ProcessTransferView11, ProcessTransferView12
from api.sct.process_deutsche_bank import deutsche_bank_transfer

# Constantes
logger = logging.getLogger("bank_services")
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = "idempotency_key"
ERROR_KEY = "error"

# ------------------------------
# Vistas CRUD para Transferencias SEPA
# ------------------------------
class SepaCreditTransferCreateView(APIView):
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(transaction_status="PDNG")
            response_data = {
                "transaction_status": transfer.transaction_status,
                "payment_id": str(transfer.payment_id),  # Ensure UUID is serialized as string
                "auth_id": str(transfer.auth_id),        # Ensure UUID is serialized as string
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SepaCreditTransferCreateView2(APIView):
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            transfer = serializer.save(transaction_status="PDNG")
            sepa_xml = generate_sepa_xml(transfer)
            media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.payment_id}.xml")
            
            with open(media_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            response_data = {
                "transaction_status": "PDNG",
                "payment_id": transfer.payment_id,
                "sepa_xml": sepa_xml
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SepaCreditTransferDetailsView(APIView):
    """
    View para obtener los detalles de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferDetailsResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferDetailsResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferDetailsResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferStatusView(APIView):
    """
    View para obtener el estado de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferCancelView(APIView):
    """
    View para cancelar una transferencia SEPA.
    """
    def delete(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            transfer.delete()
            return Response({"message": "Transfer cancelled successfully"}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferUpdateScaView(APIView):
    """
    View para actualizar el segundo factor de autenticación (SCA) de una transferencia SEPA.
    """
    def patch(self, request, payment_id):
        try:
            transfer = SepaCreditTransferUpdateScaRequest.objects.get(id=payment_id)
            serializer = SepaCreditTransferUpdateScaRequestSerializer(transfer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "SCA updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SepaCreditTransferUpdateScaRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferListView(APIView):
    """
    View para listar todas las transferencias SEPA.
    """
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelTransferView(APIView):
    """
    View para cancelar una transferencia SEPA.
    """
    def post(self, request, id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            transfer.delete()
            return Response({"message": "Transferencia cancelada exitosamente."}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transferencia con ID {id} no encontrada.", exc_info=True)  # Agregado
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado al cancelar la transferencia: {str(e)}", exc_info=True)  # Agregado
            return Response({"error": "Error inesperado al cancelar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ------------------------------
# Vistas para Descarga de Archivos
# ------------------------------
class SepaCreditTransferDownloadXmlView(APIView):
    """
    View para generar y descargar el archivo XML de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")

            # Generar el archivo XML si no existe
            if not os.path.exists(xml_path):
                sepa_xml = generate_sepa_xml(transfer)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)

            # Descargar el archivo XML
            if os.path.exists(xml_path):
                return FileResponse(open(xml_path, "rb"), content_type="application/xml", as_attachment=True, filename=f"sepa_{transfer.id}.xml")
            
            return HttpResponseNotFound("Archivo XML no encontrado.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transferencia con ID {payment_id} no encontrada.")
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al generar/descargar el archivo XML: {str(e)}", exc_info=True)
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SepaCreditTransferDownloadPdfView(APIView):
    """
    View para descargar el archivo PDF de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.id}.pdf")
            if not os.path.exists(pdf_path):
                return Response({"error": "PDF file not found"}, status=status.HTTP_404_NOT_FOUND)

            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            return Response({"pdf_content": pdf_content}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class DownloadPdfView(APIView):
    """
    View para descargar el archivo PDF de una transferencia SEPA.
    """
    def get(self, request, id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.id}.pdf")

            # Generar el archivo PDF si no existe
            if not os.path.exists(pdf_path):
                pdf_path = generar_pdf_transferencia(transfer)

            # Descargar el archivo PDF
            if os.path.exists(pdf_path):
                return FileResponse(open(pdf_path, "rb"), content_type="application/pdf", as_attachment=True, filename=f"transferencia_{transfer.id}.pdf")
            
            return HttpResponseNotFound("Archivo PDF no encontrado.")
        except SepaCreditTransferRequest.DoesNotExist:
            return HttpResponseNotFound("Transferencia no encontrada.")
        except Exception as e:
            logger.error(f"Error al generar/descargar el archivo PDF: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ------------------------------
# Vistas Basadas en Clases Genéricas
# ------------------------------
class SCTList55View(CreateView, ListView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')

    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfers'] = SepaCreditTransferRequest.objects.all()
        return context

    def form_valid(self, form):
        # Guardar la transferencia
        transfer = form.save()

        # # Procesar la transferencia
        process_view = ProcessTransferView11()
        process_view.post(self.request, idempotency_key=transfer.idempotency_key)

        return super().form_valid(form)


class SCTList6View(CreateView, ListView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')

    def get_queryset(self):
        # Define el queryset que se usará como object_list
        return SepaCreditTransferRequest.objects.all()
    
    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        # Asegurar que self.object_list esté definido
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context['transfers'] = self.object_list  # Usar self.object_list
        return context

    def form_valid(self, form):
        # Guardar la transferencia
        transfer = form.save()

        # Procesar la transferencia
        process_view = ProcessTransferView12()
        response = process_view.post(self.request, idempotency_key=transfer.idempotency_key)

        # Verificar si hubo un error
        if response.status_code != 200:
            form.add_error(None, "Error al procesar la transferencia.")
            return self.form_invalid(form)

        return super().form_valid(form)
    

class SCTList5View(CreateView, ListView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')

    def get_queryset(self):
        # Define el queryset que se usará como object_list
        return SepaCreditTransferRequest.objects.all()
    
    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        # Asegurar que self.object_list esté definido
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context['transfers'] = self.object_list  # Usar self.object_list
        return context

    def form_valid(self, form):
        # Guardar la transferencia sin procesarla
        form.save()
        return super().form_valid(form)


class SCTUpdate5View(UpdateView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_proc5.html"
    success_url = reverse_lazy('sct_list5')

    def form_valid(self, form):
        # Guardar los cambios sin salir del formulario
        self.object = form.save()
        return self.render_to_response(self.get_context_data(form=form))


class SCTEditView(UpdateView):
    """
    Vista para editar una transferencia SEPA específica.
    """
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_proc5.html"
    success_url = reverse_lazy('sct_list5')

    def form_valid(self, form):
        # Guardar los cambios realizados en la transferencia
        self.object = form.save()
        return super().form_valid(form)



# ------------------------------
# Vistas Personalizadas
# ------------------------------
def generate_and_save_xml(request, idempotency_key):
    """
    Genera y guarda un archivo XML con los datos de la transacción.
    """
    try:
        transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")

        # Generar el archivo XML
        sepa_xml = generate_sepa_xml(transfer)
        with open(xml_path, "w", encoding="utf-8") as xml_file:
            xml_file.write(sepa_xml)

        return JsonResponse({"message": "Archivo XML generado y guardado exitosamente.", "xml_path": xml_path}, status=200)
    except SepaCreditTransferRequest.DoesNotExist:
        return JsonResponse({"error": "Transferencia no encontrada."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)
    

def generate_and_save_xml2(request, idempotency_key):
    """
    Genera y guarda un archivo XML con los datos de la transacción.
    """
    try:
        transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")

        # Generar el archivo XML
        sepa_xml = generate_sepa_xml2(transfer)
        with open(xml_path, "w", encoding="utf-8") as xml_file:
            xml_file.write(sepa_xml)

        return JsonResponse({"message": "Archivo XML generado y guardado exitosamente.", "xml_path": xml_path}, status=200)
    except SepaCreditTransferRequest.DoesNotExist:
        return JsonResponse({"error": "Transferencia no encontrada."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)


def generate_and_save_xml3(request, idempotency_key):
    """
    Genera y guarda un archivo XML con los datos de la transacción.
    """
    try:
        transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")

        # Generar el archivo XML
        sepa_xml = generate_sepa_xml3(transfer)
        with open(xml_path, "w", encoding="utf-8") as xml_file:
            xml_file.write(sepa_xml)

        return JsonResponse({"message": "Archivo XML generado y guardado exitosamente.", "xml_path": xml_path}, status=200)
    except SepaCreditTransferRequest.DoesNotExist:
        return JsonResponse({"error": "Transferencia no encontrada."}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)


def generate_and_save_aml(request, idempotency_key):
    """
    Genera y guarda un archivo AMLTransactionReport con los datos de la transacción.
    """
    try:
        # Obtener la transferencia correspondiente al idempotency_key
        transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
        
        # Datos de ejemplo para el archivo AML
        transfers = {
            "transaction_id": f"TRANSFER_{transfer.idempotency_key}",
            "transaction_type": "SEPA",
            "execution_date": transfer.requested_execution_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "amount": transfer.instructed_amount,
            "currency": transfer.instructed_currency,
            "debtor_name": transfer.debtor_name,
            "debtor_iban": transfer.debtor_account_iban,
            "debtor_bic": transfer.debtor_account_bic,
            "debtor_country": transfer.debtor_adress_country,
            "debtor_customer_id": "27CDBFRDE17BEH",  # Ejemplo, puedes reemplazarlo con un campo real
            "debtor_kyc_verified": True,  # Ejemplo, puedes reemplazarlo con un campo real
            "creditor_name": transfer.creditor_name,
            "creditor_iban": transfer.creditor_account.iban,
            "creditor_bic": transfer.creditor_account.bic,
            "creditor_country": transfer.creditor_adress_country,
            "purpose": transfer.remittance_information_unstructured,
            "channel": "OnlineBanking",  # Ejemplo, puedes reemplazarlo con un campo real
            "risk_score": 12,  # Ejemplo, puedes reemplazarlo con un cálculo real
            "pep": False,  # Ejemplo, puedes reemplazarlo con un campo real
            "sanctions_check": "Passed",  # Ejemplo, puedes reemplazarlo con un campo real
            "high_risk_country": False,  # Ejemplo, puedes reemplazarlo con un campo real
            "unusual_amount": False,  # Ejemplo, puedes reemplazarlo con un campo real
            "frequent_transfers": False,  # Ejemplo, puedes reemplazarlo con un campo real
            "manual_review_required": False,  # Ejemplo, puedes reemplazarlo con un campo real
        }

        # Ruta del archivo AML
        aml_path = os.path.join(settings.MEDIA_ROOT, f"AMLTransactionReport_{transfer.idempotency_key}.xml")

        # Generar el archivo AML
        result = generate_aml_transaction_report(transfers, aml_path)

        if result.get("success"):
            return JsonResponse({"message": "Archivo AML generado y guardado exitosamente.", "aml_path": aml_path}, status=200)
        else:
            return JsonResponse({"error": result.get("error")}, status=500)

    except SepaCreditTransferRequest.DoesNotExist:
        return JsonResponse({"error": "Transferencia no encontrada."}, status=404)
    except Exception as e:
        logger.error(f"Error inesperado al generar el archivo AML: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)


def SCTSend5View(request, idempotency_key):
    """
    Vista para enviar el archivo XML de una transferencia SEPA al banco y actualizar el estado.
    """
    try:
        # Buscar la transferencia correspondiente
        transfer = get_object_or_404(SepaCreditTransferRequest, idempotency_key=idempotency_key)

        # Enviar el archivo XML al banco utilizando deutsche_bank_transfer
        bank_response = process_bank_transfer(idempotency_key, transfer)

        # Verificar si hubo un error en la respuesta del banco
        if "error" in bank_response:
            return render(request, "api/SCT/sct_send5.html", {
                "error": f"Error al enviar el archivo al banco: {bank_response['error']}"
            })

        # Renderizar la respuesta exitosa
        return render(request, "api/SCT/sct_send5.html", {
            "success": "El archivo XML fue enviado exitosamente al banco y el estado de la transferencia fue actualizado."
        })

    except Exception as e:
        logger.error(f"Error en SCTSend5View: {str(e)}", exc_info=True)
        return render(request, "api/SCT/sct_send5.html", {
            "error": f"Error inesperado: {str(e)}"
        })


def SCTSend6View(request, idempotency_key):
    """
    Vista para enviar el archivo XML y AML de una transferencia SEPA al banco y actualizar el estado.
    """
    try:
        # Buscar la transferencia correspondiente
        transfer = get_object_or_404(SepaCreditTransferRequest, idempotency_key=idempotency_key)

        # Rutas de los archivos XML y AML generados previamente
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{idempotency_key}.xml")
        aml_path = os.path.join(settings.MEDIA_ROOT, f"AMLTransactionReport_{idempotency_key}.xml")

        # Verificar si los archivos existen
        if not os.path.exists(xml_path) or not os.path.exists(aml_path):
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Los archivos XML o AML no fueron encontrados. Por favor, genere los archivos antes de enviarlos."
            })

        # Leer el contenido de los archivos XML y AML
        try:
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo XML: {str(e)}", exc_info=True)
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Error al leer el archivo XML."
            })

        try:
            with open(aml_path, "r", encoding="utf-8") as aml_file:
                aml_content = aml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo AML: {str(e)}", exc_info=True)
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Error al leer el archivo AML."
            })

        # Validar variables de entorno necesarias
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"
        refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc0NDc3OTcxOSwiaWF0IjoxNzQ0NjkzMzE5LCJqdGkiOiIxMGQ5ZDIzZjJhMjY0ZTMyOTkxYzVmNzQ2OTI4ZWVjNiIsInVzZXJfaWQiOjF9.Md5TQ8l8HNvba-GfIyqp3aj084DANR9X4ySCRZA6WwI"

        # Enviar el XML y AML al banco
        try:
            response = requests.post(
                url="https://api.db.com:443/gw/dbapi/banking/transactions/v2",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/xml",
                    "idempotency-id": str(idempotency_key),
                    # "otp": "SEPA_TRANSFER_GRANT",
                },
                data=f"{xml_content}\n{aml_content}",
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar los archivos al banco: {str(e)}", exc_info=True)
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Error al enviar los archivos al banco."
            })

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return render(request, "api/SCT/sct_send5.html", {
                "error": f"Error al enviar los archivos al banco: {response.text}"
            })

        # Procesar la respuesta del banco
        try:
            bank_response = response.text  # Asumiendo que es texto o XML
            
        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Error procesando la respuesta del banco."
            })

        # Renderizar la respuesta exitosa
        return render(request, "api/SCT/sct_send5.html", {
            "success": "Los archivos XML y AML fueron enviados exitosamente al banco y el estado de la transferencia fue actualizado."
        })

    except Exception as e:
        logger.error(f"Error en SCTSend6View: {str(e)}", exc_info=True)
        return render(request, "api/SCT/sct_send5.html", {
            "error": f"Error inesperado: {str(e)}"
        })


def SCTSend7View(request, idempotency_key):
    """
    Vista para enviar el archivo XML y AML de una transferencia SEPA al banco y actualizar el estado.
    """
    try:
        # Buscar la transferencia correspondiente
        transfer = get_object_or_404(SepaCreditTransferRequest, idempotency_key=idempotency_key)

        # Rutas de los archivos XML y AML generados previamente
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{idempotency_key}.xml")
        aml_path = os.path.join(settings.MEDIA_ROOT, f"AMLTransactionReport_{idempotency_key}.xml")

        # Verificar si los archivos existen
        if not os.path.exists(xml_path) or not os.path.exists(aml_path):
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Los archivos XML o AML no fueron encontrados. Por favor, genere los archivos antes de enviarlos."
            })

        # Leer el contenido de los archivos XML y AML
        with open(xml_path, "r", encoding="utf-8") as xml_file:
            xml_content = xml_file.read()

        with open(aml_path, "r", encoding="utf-8") as aml_file:
            aml_content = aml_file.read()


        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"
        refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc0NDc3OTcxOSwiaWF0IjoxNzQ0NjkzMzE5LCJqdGkiOiIxMGQ5ZDIzZjJhMjY0ZTMyOTkxYzVmNzQ2OTI4ZWVjNiIsInVzZXJfaWQiOjF9.Md5TQ8l8HNvba-GfIyqp3aj084DANR9X4ySCRZA6WwI"
        
        # Enviar el XML y AML al banco
        response = requests.post(
            url="https://api.db.com:443/gw/dbapi/banking/transactions/v2",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/xml",
                "idempotency-id": str(idempotency_key),
            },
            data=f"{xml_content}\n{aml_content}",
        )

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return render(request, "api/SCT/sct_send5.html", {
                "error": f"Error al enviar los archivos al banco: {response.text}"
            })

        # Procesar la respuesta del banco
        try:
            if response.headers.get("Content-Type") == "application/json":
                bank_response = response.json()
            else:
                bank_response = response.text  # Asumiendo que es XML o texto plano

            # Registrar la respuesta del banco
            logger.info(f"Respuesta del banco: {bank_response}")

            # Validar si la respuesta contiene errores
            if "error" in bank_response:
                return render(request, "api/SCT/sct_send5.html", {
                    "error": f"Error en la respuesta del banco: {bank_response['error']}"
                })

        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return render(request, "api/SCT/sct_send5.html", {
                "error": "Error procesando la respuesta del banco."
            })

        # Renderizar la respuesta exitosa
        return render(request, "api/SCT/sct_send5.html", {
            "success": "Los archivos XML y AML fueron enviados exitosamente al banco y el estado de la transferencia fue actualizado."
        })

    except Exception as e:
        logger.error(f"Error en SCTSend6View: {str(e)}", exc_info=True)
        return render(request, "api/SCT/sct_send5.html", {
            "error": f"Error inesperado: {str(e)}"
        })


def SCTSend8View(request, idempotency_key):
    """
    Vista para enviar el archivo XML de una transferencia SEPA al banco y actualizar el estado.
    """
    try:
        # Buscar la transferencia correspondiente
        transfer = get_object_or_404(SepaCreditTransferRequest, idempotency_key=idempotency_key)

        # Enviar el archivo XML al banco utilizando process_bank_transfer_json_xml_aml
        bank_response = process_bank_transfer_jsonn(idempotency_key, transfer)

        # Verificar si hubo un error en la respuesta del banco
        if "error" in bank_response:
            logger.error(f"Error al enviar el archivo al banco: {bank_response['error']}")
            return render(request, "api/SCT/sct_send5.html", {
                "error": f"Error al enviar el archivo al banco: {bank_response['error']}"
            })

        # Renderizar la respuesta exitosa
        return render(request, "api/SCT/sct_send5.html", {
            "success": "El archivo XML fue enviado exitosamente al banco y el estado de la transferencia fue actualizado."
        })

    except SepaCreditTransferRequest.DoesNotExist:
        logger.error(f"Transferencia con idempotency_key {idempotency_key} no encontrada.")
        return render(request, "api/SCT/sct_send5.html", {
            "error": "Transferencia no encontrada."
        })
    except Exception as e:
        logger.error(f"Error inesperado en SCTSend5View para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return render(request, "api/SCT/sct_send5.html", {
            "error": "Ocurrió un error inesperado al procesar la solicitud."
        })


def SCTUpdate5ListView(request):
    """
    Vista para listar y actualizar transferencias SEPA.
    """
    try:
        # Obtener todas las transferencias
        transfers = SepaCreditTransferDetailsResponse.objects.all()

        # Renderizar la plantilla con las transferencias
        return render(request, "api/SCT/sct_upda5.html", {
            "transfers": transfers
        })
    except Exception as e:
        logger.error(f"Error en SCTUpdate5ListView: {str(e)}", exc_info=True)
        return render(request, "api/SCT/sct_upda5.html", {
            "error": "Ocurrió un error al cargar las transferencias."
        })




