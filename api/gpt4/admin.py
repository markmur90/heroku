from django.contrib import admin
from api.gpt4.models import (
    Debtor,
    DebtorAccount,
    Creditor,
    CreditorAccount,
    CreditorAgent,
    PaymentIdentification,
    ClientID,
    Kid,
    Transfer,
    LogTransferencia,
    ClaveGenerada
)

class DebtorAdmin(admin.ModelAdmin):
    list_display = ('name', 'customer_id', 'postal_address_country', 'postal_address_city')
    search_fields = ('name', 'customer_id')

class DebtorAccountAdmin(admin.ModelAdmin):
    list_display = ('debtor', 'iban', 'currency')
    list_filter = ('currency',)
    search_fields = ('iban',)

class CreditorAdmin(admin.ModelAdmin):
    list_display = ('name', 'postal_address_country', 'postal_address_city')
    search_fields = ('name',)

class CreditorAccountAdmin(admin.ModelAdmin):
    list_display = ('creditor', 'iban', 'currency')
    list_filter = ('currency',)
    search_fields = ('iban',)

class CreditorAgentAdmin(admin.ModelAdmin):
    list_display = ('bic', 'financial_institution_id', 'other_information')
    search_fields = ('bic', 'financial_institution_id')

class PaymentIdentificationAdmin(admin.ModelAdmin):
    list_display = ('end_to_end_id', 'instruction_id')
    search_fields = ('end_to_end_id', 'instruction_id')

class ClientIDAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'clientId')
    search_fields = ('codigo', 'clientId')

class KidAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'kid')
    search_fields = ('codigo', 'kid')

class TransferAdmin(admin.ModelAdmin):
    list_display = (
        'payment_id',
        'client',
        'kid',
        'debtor',
        'creditor',
        'status',
        'created_at'
    )
    list_filter = ('status', 'requested_execution_date')
    search_fields = (
        'payment_id',
        'payment_identification__end_to_end_id',
        'payment_identification__instruction_id'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_select_related = (
        'client',
        'kid',
        'debtor',
        'creditor',
        'payment_identification'
    )

class LogTransferenciaAdmin(admin.ModelAdmin):
    list_display = ('registro', 'tipo_log', 'contenido', 'created_at')
    readonly_fields = ('created_at',)
    list_select_related = ('transfer',)


admin.site.register(Debtor, DebtorAdmin)
admin.site.register(DebtorAccount, DebtorAccountAdmin)
admin.site.register(Creditor, CreditorAdmin)
admin.site.register(CreditorAccount, CreditorAccountAdmin)
admin.site.register(CreditorAgent, CreditorAgentAdmin)
admin.site.register(PaymentIdentification, PaymentIdentificationAdmin)
admin.site.register(ClientID, ClientIDAdmin)
admin.site.register(Kid, KidAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(LogTransferencia, LogTransferenciaAdmin)


@admin.register(ClaveGenerada)
class ClaveGeneradaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "estado", "kid")
    list_filter = ("estado", "usuario")
    search_fields = ("usuario", "kid")

