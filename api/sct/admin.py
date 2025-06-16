from django.contrib import admin
from api.sct.models import (
    CategoryPurpose, ServiceLevel, LocalInstrument,
    SepaCreditTransferRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest,
    ErrorResponse, Address, Debtor, Creditor, Account, PaymentIdentification,
    InstructedAmount, CreditorAgent, SepaCreditTransfer
)

# Registrar los modelos
admin.site.register(CategoryPurpose)
admin.site.register(ServiceLevel)
admin.site.register(LocalInstrument)
admin.site.register(SepaCreditTransferRequest)
admin.site.register(SepaCreditTransferResponse)
admin.site.register(SepaCreditTransferDetailsResponse)
admin.site.register(SepaCreditTransferUpdateScaRequest)
admin.site.register(ErrorResponse)
admin.site.register(Address)
admin.site.register(Debtor)
admin.site.register(Creditor)
admin.site.register(Account)
admin.site.register(PaymentIdentification)
admin.site.register(InstructedAmount)
admin.site.register(CreditorAgent)
admin.site.register(SepaCreditTransfer)

