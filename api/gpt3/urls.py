# api/gpt3/urls.py

from django.urls import path

from api.gpt3.views2 import CrearBulkTransferView, EnviarBulkTransferView, EstadoBulkTransferView, account_list_view, amount_list_view, cancelar_transferencia, crear_transferencia, create_account, create_amount, create_creditor, create_debtor, create_financial_institution, create_payment_identification, create_postal_address, creditor_list_view, debtor_list_view, descargar_pdf, detalle_transferencia, enviar_transferencia, estado_transferencia, financial_institution_list_view, listar_bulk_transferencias, listar_transferencias, postal_address_list_view, retry_second_factor_view


urlpatterns = [
    # Transferencias individuales
    path('transferencias/crear/', crear_transferencia, name='crear_transferenciaGPT3'),
    path('transferencias/', listar_transferencias, name='listar_transferenciasGPT3'),
    path('transferencias/<str:payment_id>/', detalle_transferencia, name='detalle_transferenciaGPT3'),
    path('transferencias/enviar/<str:payment_id>/', enviar_transferencia, name='enviar_transferenciaGPT3'),
    path('transferencias/estado/<str:payment_id>/', estado_transferencia, name='estado_transferenciaGPT3'),
    path('transferencias/cancelar/<str:payment_id>/', cancelar_transferencia, name='cancelar_transferenciaGPT3'),
    path('transferencias/reintentar/<str:payment_id>/', retry_second_factor_view, name='retry_second_factorGPT3'),

    # Transferencias bulk
    path('bulk/', listar_bulk_transferencias, name='listar_bulkGPT3'),
    path('bulk/crear/', CrearBulkTransferView, name='crear_bulkGPT3'),
    path('bulk/enviar/<str:payment_id>/', EnviarBulkTransferView, name='enviar_bulkGPT3'),
    path('bulk/estado/<str:payment_id>/', EstadoBulkTransferView, name='estado_bulkGPT3'),
    # path('bulk/detalle/<str:payment_id>/', DetalleBulkTransferView, name='detalle_transferencia_bulkGPT3'),

    # Crear entidades auxiliares
    path('cuentas/crear/', create_account, name='create_accountGPT3'),
    path('montos/crear/', create_amount, name='create_amountGPT3'),
    path('instituciones/crear/', create_financial_institution, name='create_financial_institutionGPT3'),
    path('direcciones/crear/', create_postal_address, name='create_postal_addressGPT3'),
    path('pagos/crear/', create_payment_identification, name='create_payment_identificationGPT3'),
    path('deudores/crear/', create_debtor, name='create_debtorGPT3'),
    path('acreedores/crear/', create_creditor, name='create_creditorGPT3'),

    # Listados auxiliares
    path('cuentas/', account_list_view, name='account_listGPT3'),
    path('montos/', amount_list_view, name='amount_listGPT3'),
    path('instituciones/', financial_institution_list_view, name='financial_institution_listGPT3'),
    path('direcciones/', postal_address_list_view, name='postal_address_listGPT3'),
    path('deudores/', debtor_list_view, name='debtor_listGPT3'),
    path('acreedores/', creditor_list_view, name='creditor_listGPT3'),
    
    path('<str:payment_id>/pdf/', descargar_pdf, name='descargar_pdfGPT3'),
]
