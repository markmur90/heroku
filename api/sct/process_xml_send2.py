import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.sct.helpers import generate_deterministic_id, generate_payment_id
from config import settings
from lxml import etree
from api.sct.models import *
from api.sct.forms import SepaCreditTransferForm
import requests
import uuid
from datetime import datetime
from requests_oauthlib import OAuth2Session
import logging
from pytz import timezone  # Importar módulo para manejo de zonas horarias
# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'

CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

# Configuración Namespaces XML
PAIN_001_NSMAP = {
    None: 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

PAIN_002_NSMAP = {
    None: 'urn:iso:std:iso:20022:tech:xsd:pain.002.001.03'
}

# Configuración OAuth2
OAUTH_CONFIG = {
    'client_id': str(CLIENT_ID),
    'client_secret': str(CLIENT_SECRET),
    'token_url': 'https://api.db.com/gw/oidc/token',
    'authorization_url': 'https://api.db.com/gw/oidc/authorize',
    'scopes': ['sepa_credit_transfers']
}


# def get_oauth_session(request):
#     """Crea sesión OAuth2 con token almacenado en sesión"""
#     token = request.session.get('oauth_token')
#     if not token or datetime.utcnow() >= datetime.fromtimestamp(token['expires_at']):
#         # Renovar token
#         oauth = OAuth2Session(client_id=OAUTH_CONFIG['client_id'])
#         token = oauth.refresh_token(OAUTH_CONFIG['token_url'], refresh_token=token['refresh_token'])
#         request.session['oauth_token'] = token
#     return OAuth2Session(client_id=OAUTH_CONFIG['client_id'], token=token)


def get_oauth_session(request):
    """Crea sesión OAuth2 utilizando el access_token del entorno"""
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN no está configurado en las variables de entorno")
        raise ValueError("ACCESS_TOKEN no está configurado")

    # Crear sesión OAuth2 con el token de acceso
    return OAuth2Session(client_id=OAUTH_CONFIG['client_id'], token={'access_token': ACCESS_TOKEN, 'token_type': 'Bearer'})


def validate_xml(xml_data, xsd_path):
    """Valida el XML contra un esquema XSD"""
    try:
        if not os.path.exists(xsd_path):
            logger.error(f"Archivo XSD no encontrado en la ruta: {xsd_path}")
            raise FileNotFoundError(f"Archivo XSD no encontrado: {xsd_path}")

        with open(xsd_path, 'rb') as xsd_file:
            schema = etree.XMLSchema(etree.parse(xsd_file))
            parser = etree.XMLParser(schema=schema)
            etree.fromstring(xml_data, parser)
        logger.info("XML validado correctamente")
        return True
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except etree.XMLSyntaxError as e:
        logger.error(f"Error de sintaxis XML: {str(e)}")
        return False
    except etree.DocumentInvalid as e:
        logger.error(f"Error de validación contra el esquema XSD: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado durante la validación XML: {str(e)}")
        return False
    

def generate_pain_001(transfer):
    """Genera XML pain.001.001.03 completo"""
    try:
        # Validar campos requeridos
        if not transfer.payment_id or not transfer.instructed_amount or not transfer.debtor:
            raise ValueError("Faltan campos requeridos en la transferencia")

        # Elemento raíz
        doc = etree.Element('Document', nsmap=PAIN_001_NSMAP)
        doc.set('{%s}schemaLocation' % PAIN_001_NSMAP['xsi'], 
               'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03 pain.001.001.03.xsd')

        # Cabecera del mensaje
        cstmr_cdt_trf_initn = etree.SubElement(doc, 'CstmrCdtTrfInitn')

        # Grupo Header
        grp_hdr = etree.SubElement(cstmr_cdt_trf_initn, 'GrpHdr')
        msg_id = etree.SubElement(grp_hdr, 'MsgId').text = str(transfer.payment_id)
        
        # Obtener la fecha y hora actual en la zona horaria de Frankfurt
        frankfurt_tz = timezone('Europe/Berlin')
        cre_dt_tm = etree.SubElement(grp_hdr, 'CreDtTm').text = datetime.now(frankfurt_tz).isoformat()
        
        nb_of_txs = etree.SubElement(grp_hdr, 'NbOfTxs').text = '1'
        ctrl_sum = etree.SubElement(grp_hdr, 'CtrlSum').text = str(transfer.instructed_amount.amount)
        initg_pty = etree.SubElement(grp_hdr, 'InitgPty')
        nm = etree.SubElement(initg_pty, 'Nm').text = transfer.debtor.debtor_name

        # Información de pago
        pmt_inf = etree.SubElement(cstmr_cdt_trf_initn, 'PmtInf')
        pmt_inf_id = etree.SubElement(pmt_inf, 'PmtInfId').text = str(transfer.payment_id)
        pmt_mtd = etree.SubElement(pmt_inf, 'PmtMtd').text = 'TRF'
        btch_bookg = etree.SubElement(pmt_inf, 'BtchBookg').text = 'false'
        nb_of_txs = etree.SubElement(pmt_inf, 'NbOfTxs').text = '1'
        ctrl_sum = etree.SubElement(pmt_inf, 'CtrlSum').text = str(transfer.instructed_amount.amount)

        # Fecha de ejecución solicitada
        reqd_exctn_dt = etree.SubElement(pmt_inf, 'ReqdExctnDt').text = transfer.requested_execution_date.isoformat()

        # Código de propósito
        if transfer.purpose_code:
            etree.SubElement(pmt_inf, 'Purp').text = transfer.purpose_code

        # Información del deudor
        dbtr = etree.SubElement(pmt_inf, 'Dbtr')
        etree.SubElement(dbtr, 'Nm').text = transfer.debtor.debtor_name
        if transfer.debtor.debtor_postal_address:
            addr = etree.SubElement(dbtr, 'PstlAdr')
            etree.SubElement(addr, 'Ctry').text = transfer.debtor.debtor_postal_address.country
            etree.SubElement(addr, 'AdrLine').text = transfer.debtor.debtor_postal_address.street_and_house_number
            etree.SubElement(addr, 'AdrLine').text = transfer.debtor.debtor_postal_address.zip_code_and_city

        # Cuenta del deudor
        dbtr_acct = etree.SubElement(pmt_inf, 'DbtrAcct')
        id = etree.SubElement(dbtr_acct, 'Id')
        etree.SubElement(id, 'IBAN').text = transfer.debtor_account.iban
        etree.SubElement(dbtr_acct, 'Ccy').text = transfer.debtor_account.currency

        # Agente del acreedor
        if transfer.creditor_agent:
            cdtr_agt = etree.SubElement(pmt_inf, 'CdtrAgt')
            fin_instn_id = etree.SubElement(cdtr_agt, 'FinInstnId')
            etree.SubElement(fin_instn_id, 'BIC').text = transfer.creditor_agent.financial_institution_id

        # Instrucciones de pago
        cdt_trf_tx_inf = etree.SubElement(pmt_inf, 'CdtTrfTxInf')
        pmt_id = etree.SubElement(cdt_trf_tx_inf, 'PmtId')
        etree.SubElement(pmt_id, 'EndToEndId').text = transfer.end_to_end_id
        amt = etree.SubElement(cdt_trf_tx_inf, 'Amt')
        instructed_amt = etree.SubElement(amt, 'InstdAmt', Ccy=transfer.instructed_amount.currency)
        instructed_amt.text = str(transfer.instructed_amount.amount)

        # Información del beneficiario
        cdtr = etree.SubElement(cdt_trf_tx_inf, 'Cdtr')
        etree.SubElement(cdtr, 'Nm').text = transfer.creditor.creditor_name
        if transfer.creditor.creditor_postal_address:
            addr = etree.SubElement(cdtr, 'PstlAdr')
            etree.SubElement(addr, 'Ctry').text = transfer.creditor.creditor_postal_address.country
            etree.SubElement(addr, 'AdrLine').text = transfer.creditor.creditor_postal_address.street_and_house_number
            etree.SubElement(addr, 'AdrLine').text = transfer.creditor.creditor_postal_address.zip_code_and_city

        # Cuenta del beneficiario
        cdtr_acct = etree.SubElement(cdtr, 'CdtrAcct')
        id = etree.SubElement(cdtr_acct, 'Id')
        etree.SubElement(id, 'IBAN').text = transfer.creditor_account.iban

        # Información adicional
        if transfer.remittance_information_unstructured:
            rmt_inf = etree.SubElement(cdt_trf_tx_inf, 'RmtInf')
            etree.SubElement(rmt_inf, 'Ustrd').text = transfer.remittance_information_unstructured

        # Convertir el documento a cadena XML
        xml_data = etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8')

        # Guardar el archivo en el directorio schemas
        schemas_dir = os.path.join(settings.BASE_DIR, 'schemas')
        os.makedirs(schemas_dir, exist_ok=True)  # Crear el directorio si no existe
        file_path = os.path.join(schemas_dir, f"pain_001_001_03_{transfer.payment_id}.xml")
        with open(file_path, 'wb') as f:
            f.write(xml_data)

        logger.info(f"Archivo XML generado y guardado en: {file_path}")
        return xml_data

    except ValueError as e:
        logger.error(f"Error en los datos de la transferencia: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error generando XML: {str(e)}")
        raise



@require_http_methods(["GET", "POST"])
def initiate_sepa_transfer(request):
    """Vista para iniciar transferencia SEPA"""
    if request.method == 'POST':
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json'
        }
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                # Guardar transferencia con estado inicial
                transfer = form.save(commit=False)
                transfer.payment_id = uuid.uuid4()
                transfer.auth_id = uuid.uuid4()
                transfer.transaction_status = 'PDNG'
                transfer.end_to_end_id = generate_payment_id()
                transfer.instruction_id = generate_deterministic_id(
                        transfer.creditor_account.iban,
                        transfer.instructed_amount.amount,
                        transfer.requested_execution_date
                    )
                transfer.save()
                
                # Generar XML pain.001
                xml_data = generate_pain_001(transfer)
                
                # # Validar XML desde el archivo generado
                # xml_file_path = os.path.join(settings.BASE_DIR, 'schemas', f"pain_001_001_03_{transfer.payment_id}.xml")
                # if not validate_xml(open(xml_file_path, 'rb').read(), os.path.join(settings.BASE_DIR, 'schemas', 'pain.001.001.03.xsd')):
                #     return HttpResponseBadRequest("XML no válido")
                
                # Configurar headers
                headers.update({
                    'Content-Type': 'application/xml',
                    'otp': request.POST.get('otp', 'SEPA_TRANSFER_GRANT'),
                    'Correlation-ID': str(uuid.uuid4()),
                    'Authorization': f"Bearer {ACCESS_TOKEN}",
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': str(ORIGIN),
                })

                # Obtener sesión OAuth2
                oauth = get_oauth_session(request)
                response = oauth.post(
                    'https://api.db.com:443/gw/dbapi/banking/transactions/v2',
                    data=xml_data,
                    headers=headers
                )

                # Procesar respuesta
                if response.status_code == 201:
                    logger.info(f"Transferencia {transfer.payment_id} enviada exitosamente")
                    return render(request, 'api/SCT/transfer_success.html', {
                        'payment_id': transfer.payment_id
                    })
                else:
                    ErrorResponse.objects.create(
                        code=response.status_code,
                        message=response.text,
                        message_id=headers['idempotency-id']
                    )
                    logger.error(f"Error del banco: {response.text}")
                    return HttpResponseBadRequest("Error en la operación bancaria")

            except Exception as e:
                ErrorResponse.objects.create(
                    code=500,
                    message=str(e),
                    message_id=headers.get('idempotency-id', '')
                )
                logger.exception("Error interno procesando transferencia")
                return HttpResponseServerError("Error interno del servidor")
    else:
        form = SepaCreditTransferForm()

    return render(request, 'api/SCT/initiate_transfer.html', {'form': form})



@csrf_exempt
@require_http_methods(["POST"])
def bank_notification(request):
    """Endpoint para recibir notificaciones pain.002 del banco"""
    try:
        # Parsear XML recibido
        root = etree.fromstring(request.body)
        
        # Extraer datos principales
        payment_id = root.xpath('//OrgnlTxRef/Id/text()', namespaces=PAIN_002_NSMAP)[0]
        status = root.xpath('//TxSts/text()', namespaces=PAIN_002_NSMAP)[0]
        
        # Actualizar transferencia
        transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
        transfer.transaction_status = status
        transfer.save()
        
        logger.info(f"Estado actualizado para {payment_id}: {status}")
        return HttpResponse("Notificación procesada exitosamente")

    except SepaCreditTransfer.DoesNotExist:
        logger.error(f"Transferencia no encontrada: {payment_id}")
        return HttpResponseBadRequest("Transferencia no existe")
    
    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error procesando notificación: {str(e)}"
        )
        logger.exception("Error procesando notificación bancaria")
        return HttpResponseServerError("Error procesando notificación")



def check_transfer_status(request, payment_id):
    """Consulta estado de transferencia y actualiza desde el banco si es necesario"""
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
        
        # Consultar estado al banco
        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json'
        }
        
        response = oauth.get(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}/status',
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            transfer.transaction_status = data.get('transactionStatus', transfer.transaction_status)
            transfer.save()

        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'bank_response': response.json() if response.ok else None
        })

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error consultando estado: {str(e)}"
        )
        logger.exception("Error consultando estado de transferencia")
        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'error': str(e)
        })


# def transfer_list(request):
#     """Listado de todas las transferencias"""
#     transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    
#     # Agregar información de estado para la plantilla
#     for transfer in transfers:
#         transfer.status_display = transfer.get_transaction_status_display()
#         transfer.status_color = transfer.get_status_color()
    
#     return render(request, 'api/SCT/transfer_list2.html', {
#         'transfers': transfers
#     })
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def transfer_list(request):
    """Listado de todas las transferencias con paginación"""
    transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    
    # Configurar paginación
    page = request.GET.get('page', 1)  # Obtener el número de página de la URL
    paginator = Paginator(transfers, 10)  # Mostrar 10 transferencias por página

    try:
        transfers_paginated = paginator.page(page)
    except PageNotAnInteger:
        transfers_paginated = paginator.page(1)  # Mostrar la primera página si el número de página no es válido
    except EmptyPage:
        transfers_paginated = paginator.page(paginator.num_pages)  # Mostrar la última página si el número es demasiado alto

    # Agregar información de estado para la plantilla
    for transfer in transfers_paginated:
        transfer.status_display = transfer.get_transaction_status_display()
        transfer.status_color = transfer.get_status_color()
    
    return render(request, 'api/SCT/transfer_list2.html', {
        'transfers': transfers_paginated
    })



# views.py
from django.shortcuts import get_object_or_404

def transfer_success(request, payment_id):
    """Vista de confirmación de transferencia exitosa"""
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    
    context = {
        'payment_id': transfer.payment_id,
        'debtor': transfer.debtor.debtor_name,
        'creditor': transfer.creditor.creditor_name,
        'amount': f"{transfer.instructed_amount.amount} {transfer.instructed_amount.currency}",
        'execution_date': transfer.requested_execution_date
    }
    
    return render(request, 'api/SCT/transfer_success.html', context)


from django.shortcuts import render, redirect
from .forms import AddressForm, DebtorForm, AccountForm, CreditorForm, CreditorAgentForm, InstructedAmountForm


def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = DebtorForm()
    return render(request, 'api/SCT/create_debtor.html', {'form': form})


def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = AccountForm()
    return render(request, 'api/SCT/create_account.html', {'form': form})


def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = CreditorForm()
    return render(request, 'api/SCT/create_creditor.html', {'form': form})


def create_creditor_agent(request):
    if request.method == 'POST':
        form = CreditorAgentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = CreditorAgentForm()
    return render(request, 'api/SCT/create_creditor_agent.html', {'form': form})


def create_instructed_amount(request):
    if request.method == 'POST':
        form = InstructedAmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = InstructedAmountForm()
    return render(request, 'api/SCT/create_instructed_amount.html', {'form': form})


def create_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transfer2')
    else:
        form = AddressForm()
    return render(request, 'api/SCT/create_address.html', {'form': form})




from django.http import FileResponse
from .generate_pdf import generar_pdf_transferencia


def generate_transfer_pdf(request, payment_id):
    """Genera un PDF para una transferencia específica"""
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    pdf_path = generar_pdf_transferencia(transfer)
    return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"{transfer.payment_id}.pdf")


@require_http_methods(["DELETE"])
def delete_transfer(request, payment_id):
    """Elimina una transferencia SEPA por su payment_id."""
    try:
        transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
        transfer.delete()
        logger.info(f"Transferencia eliminada: {payment_id}")
        return redirect('api/SCT/transfer_list2.html')  # Redirigir al listado de transferencias
    except SepaCreditTransfer.DoesNotExist:
        logger.error(f"Transferencia no encontrada: {payment_id}")
        return HttpResponseBadRequest("Transferencia no existe")
    except Exception as e:
        logger.exception("Error eliminando transferencia")
        return HttpResponseServerError("Error eliminando transferencia")