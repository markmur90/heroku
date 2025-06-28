from django.db import models
import uuid

class PostalAddress(models.Model):
    country = models.CharField(max_length=2)
    zip_code_and_city = models.CharField(max_length=100)
    street_and_house_number = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.country} - {self.street_and_house_number} - {self.zip_code_and_city}"
    

class Debtor(models.Model):
    debtor_name = models.CharField(max_length=100, blank=True, null=True, unique=True)
    postal_address = models.ForeignKey(PostalAddress, on_delete=models.CASCADE, related_name='debtor_addresses', null=True, blank=True)

    def __str__(self):
        
        return self.debtor_name


class Creditor(models.Model):
    creditor_name = models.CharField(max_length=100, blank=True, null=True, unique=True)
    postal_address = models.ForeignKey(PostalAddress, on_delete=models.CASCADE, related_name='creditor_addresses', null=True, blank=True)

    def __str__(self):
        return self.creditor_name
    

class Account(models.Model):
    iban = models.CharField(max_length=34, unique=True)
    currency = models.CharField(max_length=3, default='EUR')
    
    def __str__(self):
        return f"{self.iban} - {self.currency}"
    

class FinancialInstitution(models.Model):
    financial_institution_id = models.CharField(max_length=11, unique=True)
    
    def __str__(self):
        return self.financial_institution_id


class Amount(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')

    def __str__(self):
        return f"{self.currency} - {self.amount}"


class PaymentIdentification(models.Model):
    end_to_end_id = models.CharField(max_length=35)
    instruction_id = models.CharField(max_length=35)


class SepaCreditTransfer(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_id = models.UUIDField(default=uuid.uuid4)
    transaction_status = models.CharField(max_length=10, choices=[
        ('PDNG', 'Pendiente'),
        ('ACSC', 'Aceptado'),
        ('RJCT', 'Rechazado'),
        ('CANC', 'Cancelado')
    ], default='PDNG')

    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, related_name='debtor_transfers')
    debtor_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debtor_accounts')
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='creditor_transfers')
    creditor_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='creditor_accounts')
    creditor_agent = models.ForeignKey(FinancialInstitution, on_delete=models.SET_NULL, null=True, blank=True)

    instructed_amount = models.ForeignKey(Amount, on_delete=models.CASCADE)
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)

    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)

    payment_identification = models.OneToOneField(PaymentIdentification, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True)

    def get_transaction_status_display(self):
        return dict(SepaCreditTransfer._meta.get_field('transaction_status').choices).get(self.transaction_status, 'Desconocido')

    def get_status_color(self):
        return {
            'PDNG': 'warning',
            'ACSC': 'success',
            'RJCT': 'danger',
            'CANC': 'secondary'
        }.get(self.transaction_status, 'dark')

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('check_statusGPT', args=[str(self.payment_id)])

class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.TextField()
    message_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
