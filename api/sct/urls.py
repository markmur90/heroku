from django.urls import path
from api.sct.process_transfer import ProcessTransferView12
from api.sct.views import (
    DownloadPdfView,
    SCTSend5View,
    SCTSend6View,
    SCTSend7View,
    SCTSend8View,
    SCTUpdate5View,
    SepaCreditTransferCreateView,
    SepaCreditTransferCreateView2,
    SepaCreditTransferDetailsView,
    SepaCreditTransferStatusView,
    SepaCreditTransferCancelView,
    SepaCreditTransferUpdateScaView,
    SepaCreditTransferListView,
    SepaCreditTransferDownloadXmlView,
    SepaCreditTransferDownloadPdfView,
    SCTList5View,
    SCTEditView,
    SCTUpdate5ListView,
    generate_and_save_aml,
    generate_and_save_xml,
    generate_and_save_xml2,
    generate_and_save_xml3
)
from api.sct.services import SCTCreateView, SCTList, SCTView, SepaCreditTransferCreateView3, SCTLView
from api.sct.process_xml_send2 import transfer_list, initiate_sepa_transfer, bank_notification, check_transfer_status, transfer_success, create_account, create_debtor, create_creditor, create_creditor_agent, create_instructed_amount, create_address, generate_transfer_pdf, delete_transfer


# Core API Endpoints
core_urlpatterns = [
    # Base SEPA Credit Transfer endpoints
    path('', SepaCreditTransferCreateView.as_view(), name='create_sepa_credit_transfer'),
    path('v2/', SepaCreditTransferCreateView2.as_view(), name='create_sepa_credit_transfer2'),
    path('list/', SepaCreditTransferListView.as_view(), name='list_sepa_credit_transfers'),
    
    # Detail operations
    path('<uuid:payment_id>/', SepaCreditTransferDetailsView.as_view(), name='get_sepa_credit_transfer_details'),
    path('<uuid:payment_id>/status/', SepaCreditTransferStatusView.as_view(), name='get_sepa_credit_transfer_status'),
    path('<uuid:payment_id>/cancel/', SepaCreditTransferCancelView.as_view(), name='cancel_sepa_credit_transfer'),
    path('<uuid:payment_id>/update-sca/', SepaCreditTransferUpdateScaView.as_view(), name='update_sca_sepa_credit_transfer'),
    
    # File download endpoints
    path('<uuid:payment_id>/download-xml/', SepaCreditTransferDownloadXmlView.as_view(), name='download_sepa_credit_transfer_xml'),
    path('<uuid:payment_id>/download-pdf/', SepaCreditTransferDownloadPdfView.as_view(), name='download_sepa_credit_transfer_pdf'),
]

# Service API Endpoints
service_urlpatterns = [
    path('list0/', SCTCreateView.as_view(), name='sct_list0'),
    path('list1/', SCTList.as_view(), name='sct_list1'),
    path('list2/', SCTView.as_view(), name='sct_list2'),
    path('list3/', SepaCreditTransferCreateView3.as_view(), name='sct_list3'),
    path('list4/', SCTLView.as_view(), name='sct_list4'),
]

# HTML Service Endpoints
html_urlpatterns = [
    # HTML SERVICES
    path('list5/', SCTList5View.as_view(), name='sct_list5'),
    path('download-pdf/<int:id>/', DownloadPdfView.as_view(), name='download_pdf'),
    path('proc5/<uuid:pk>/', SCTUpdate5View.as_view(), name='sct_proc5'),
    path('process/<uuid:idempotency_key>/', ProcessTransferView12.as_view(), name='process_transfer'),
    path('edit/<int:pk>/', SCTEditView.as_view(), name='sct_edit'),
    path('generate-xml/<uuid:idempotency_key>/', generate_and_save_xml, name='generate_xml'),
    path('generate2-xml/<uuid:idempotency_key>/', generate_and_save_xml2, name='generate_xml2'),
    path('generate3-xml/<uuid:idempotency_key>/', generate_and_save_xml3, name='generate_xml3'),
    path('generate-aml/<str:idempotency_key>/', generate_and_save_aml, name='generate_aml'),
    path('send/<uuid:idempotency_key>/', SCTSend8View, name='sct_send5'),
    path('update5/', SCTUpdate5ListView, name='sct_update5'),
    
]

html2_urlpatterns = [
    path('list22', transfer_list, name='transfer_list22'),
    path('initiate/', initiate_sepa_transfer, name='initiate_transfer2'),
    path('bank-notification/', bank_notification, name='bank_notification2'),
    path('status/<uuid:payment_id>/', check_transfer_status, name='check_status2'),
    path('success/<uuid:payment_id>/', transfer_success, name='transfer_success2'),
    path('generate-pdf/<uuid:payment_id>/', generate_transfer_pdf, name='generate_transfer_pdf'),
    path('delete/<uuid:payment_id>/', delete_transfer, name='delete_transfer'),
]

html3_urlpatterns = [
    path('create-debtor/', create_debtor, name='create_debtor'),
    path('create-account/', create_account, name='create_account'),
    path('create-creditor/', create_creditor, name='create_creditor'),
    path('create-creditor-agent/', create_creditor_agent, name='create_creditor_agent'),
    path('create-instructed-amount/', create_instructed_amount, name='create_instructed_amount'),
    path('create-address/', create_address, name='create_address'),

]

# Combined URL patterns
urlpatterns = core_urlpatterns + service_urlpatterns + html_urlpatterns + html2_urlpatterns + html3_urlpatterns