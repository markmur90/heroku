from django.urls import path
from . import views

urlpatterns = [
    # Iniciar transferencia
    path('transfer/initiate/', views.initiate_sepa_transfer, name='initiate_transferGPT'),

    # Ver estado
    path('transfer/<uuid:payment_id>/status/', views.check_transfer_status, name='check_statusGPT'),

    # Listado general
    path('transfer/list/', views.transfer_list_view, name='transfer_listGPT'),

    # Eliminar transferencia
    path('transfer/<uuid:payment_id>/delete/', views.delete_transfer, name='delete_transferGPT'),

    # Descargar PDF
    path('transfer/<uuid:payment_id>/pdf/', views.generate_transfer_pdf, name='generate_transfer_pdfGPT'),

    # 🔁 Cancelar transferencia (DELETE)
    path('transfer/<uuid:payment_id>/cancel/', views.cancel_sepa_transfer, name='cancel_transferGPT'),

    # 🔁 Retry segundo factor TAN (PATCH)
    path('transfer/<uuid:payment_id>/retry-auth/', views.retry_sepa_transfer_auth, name='retry_transfer_authGPT'),

    # Éxito de cancelación
    path('transfer/<uuid:payment_id>/cancel-success/', views.cancel_success_view, name='cancel_successGPT'),

    # Crear Account
    path('create/account/', views.create_account, name='create_accountGPT'),

    # Crear Amount
    path('create/amount/', views.create_amount, name='create_amountGPT'),

    # Crear Financial Institution
    path('create/financial-institution/', views.create_financial_institution, name='create_financial_institutionGPT'),

    # Crear Postal Address
    path('create/postal-address/', views.create_postal_address, name='create_postal_addressGPT'),

    # Crear Payment Identification
    path('create/payment-identification/', views.create_payment_identification, name='create_payment_identificationGPT'),

    # Crear Debtor
    path('create/debtor/', views.create_debtor, name='create_debtorGPT'),

    # Crear Creditor
    path('create/creditor/', views.create_creditor, name='create_creditorGPT'),
]

