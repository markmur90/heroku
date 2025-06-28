from django.contrib import admin
from .models import (
    SepaCreditTransfer, Account, Amount,
    FinancialInstitution, PostalAddress, PaymentIdentification,
    ErrorResponse
)

@admin.register(SepaCreditTransfer)
class SepaCreditTransferAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'transaction_status', 'debtor', 'creditor', 'requested_execution_date', 'created_at')
    list_filter = ('transaction_status',)
    search_fields = ('payment_id', 'debtor__debtor_name', 'creditor__creditor_name')

admin.site.register(Account)
admin.site.register(Amount)
admin.site.register(FinancialInstitution)
admin.site.register(PostalAddress)
admin.site.register(PaymentIdentification)
admin.site.register(ErrorResponse)
