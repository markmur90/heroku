from django.urls import path
from api.gpt4 import views

urlpatterns = [
    # Debtor
    path('debtors/create/', views.create_debtor, name='create_debtorGPT4'),
    path('debtors/', views.list_debtors, name='list_debtorsGPT4'),
    
    path('debtor-accounts/create/', views.create_debtor_account, name='create_debtor_accountGPT4'),
    path('debtor-accounts/', views.list_debtor_accounts, name='list_debtor_accountsGPT4'),

    # Creditor
    path('creditors/create/', views.create_creditor, name='create_creditorGPT4'),
    path('creditors/', views.list_creditors, name='list_creditorsGPT4'),
    
    path('creditor-accounts/create/', views.create_creditor_account, name='create_creditor_accountGPT4'),
    path('creditor-accounts/', views.list_creditor_accounts, name='list_creditor_accountsGPT4'),
    
    path('creditor-agents/create/', views.create_creditor_agent, name='create_creditor_agentGPT4'),
    path('creditor-agents/', views.list_creditor_agents, name='list_creditor_agentsGPT4'),

    path('clientids/create/', views.create_clientid, name='create_clientidGPT4'),
    path('kids/create/', views.create_kid, name='create_kidGPT4'),

    # Transfers
    # path('transfers/create/', views.create_transfer, name='create_transferGPT4'),
    # path('transfers/<int:transfer_id>/send/', views.send_transfer_view, name='send_transfer_viewGPT4'),
    # path('transfer/<str:payment_id>/sca/', views.transfer_update_sca, name='transfer_update_scaGPT4'),
    
    
    path('transfers/<str:payment_id>/pdf/', views.descargar_pdf, name='descargar_pdfGPT4'),

    path("transfers/<str:payment_id>/edit/", views.edit_transfer, name="edit_transferGPT4"),
    path("transfers/create/", views.create_transfer, name="create_transferGPT4"),
    path("transfers/<str:payment_id>/send/", views.send_transfer_view, name="send_transfer_viewGPT4"),
    path("transfers/<str:payment_id>/send-banco/", views.send_transfer_conexion_view, name="send_transfer_conexion_viewGPT4"),
    path("transfers/<str:payment_id>/send-simulador/", views.send_transfer_simulator_view, name="send_transfer_simulator_viewGPT4"),
    path("transfers/<str:payment_id>/send-fake/", views.send_transfer_fake_view, name="send_transfer_fake_viewGPT4"),
    # path("transfers/<str:payment_id>/send/", views.send_transfer_view4, name="send_transfer_viewGPT4"),
    path("transfers/<str:payment_id>/sca/", views.transfer_update_sca, name="transfer_update_scaGPT4"),
    path("transfers/<str:payment_id>/", views.transfer_detail, name="transfer_detailGPT4"),
    

    path('toggle-oauth/', views.toggle_oauth, name='toggle_oauth'),
    path('oauth2/logs/', views.get_oauth_logs, name='get_oauth_logs'),
    path("logs/", views.list_logs, name="list_logsGPT4"),
    path("oauth2/log-visual/", views.log_oauth_visual_inicio, name="log_oauth_visual_inicio"),
    path('transfers/notificaciones/', views.handle_notification, name='handle_notification'),  # hipotético
    
    path('', views.ClaveGeneradaListView.as_view(), name='lista_claves'),
    path('crear/', views.ClaveGeneradaCreateView.as_view(), name='crear_clave'),
    path('editar/<int:pk>/', views.ClaveGeneradaUpdateView.as_view(), name='editar_clave'),
    path('eliminar/<int:pk>/', views.ClaveGeneradaDeleteView.as_view(), name='eliminar_clave'),
    path("toggle_banco/", views.toggle_conexion_banco, name="toggle_conexion_banco"),
    path("probar_banco/", views.prueba_conexion_banco, name="prueba_conexion_banco"),
    path("diagnostico_banco/", views.diagnostico_banco, name="diagnostico_banco"),
    path("api/bank_sim/token", views.bank_sim_token, name="bank_sim_token"),
    path("api/bank_sim/challenge", views.bank_sim_challenge, name="bank_sim_challenge"),
    path("api/bank_sim/send-transfer", views.bank_sim_send_transfer, name="bank_sim_send_transfer"),
    path("api/bank_sim/status-transfer", views.bank_sim_status_transfer, name="bank_sim_status_transfer"),
    
    path("simular_transferencia/", views.SimulacionTransferenciaView.as_view(), name="simular_transferencia"),


]