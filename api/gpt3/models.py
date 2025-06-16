from django.db import models
import uuid


class Address(models.Model):
    country = models.CharField(max_length=2)
    street_and_house_number = models.CharField(max_length=70)
    zip_code_and_city = models.CharField(max_length=70)

    def __str__(self):
        return f"{self.country}, {self.zip_code_and_city}, {self.street_and_house_number}"


class Debtor(models.Model):
    debtor_name = models.CharField(max_length=70, unique=True, blank=False, default='MIRYA TRADING CO LTD')
    postal_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    customer_id = models.CharField(max_length=35, unique=True, blank=False, default='090512DEUTDEFFXXX886479')

    def __str__(self):
        return self.debtor_name


class Creditor(models.Model):
    creditor_name = models.CharField(max_length=70)
    postal_address = models.ForeignKey(Address, on_delete=models.CASCADE)

    def __str__(self):
        return self.creditor_name


class Account(models.Model):
    iban = models.CharField(max_length=34)
    currency = models.CharField(max_length=3, default='EUR')

    def __str__(self):
        return f"{self.iban} ({self.currency})"


class FinancialInstitution(models.Model):
    financial_institution_id = models.CharField(max_length=35)

    def __str__(self):
        return self.financial_institution_id


class PaymentIdentification(models.Model):
    end_to_end_id = models.CharField(max_length=35)
    instruction_id = models.CharField(max_length=35)

    def __str__(self):
        return self.end_to_end_id


class InstructedAmount(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')

    def __str__(self):
        return f"{self.currency} - {self.amount}"
   

class SepaCreditTransfer(models.Model):
    payment_id = models.CharField(max_length=36, unique=True)
    auth_id = models.CharField(max_length=36, blank=True, null=True)
    transaction_status = models.CharField(max_length=10, default='PDNG', choices=[
        ('RJCT', 'Rechazada'),
        ('RCVD', 'Recibida'),
        ('ACCP', 'Aceptada'),
        ('ACTC', 'Aceptada técnicamente'),
        ('ACSP', 'En proceso'),
        ('ACSC', 'Ejecutada con éxito'),
        ('ACWC', 'Con advertencia'),
        ('ACWP', 'Pendiente de aprobación'),
        ('ACCC', 'Concluida'),
        ('CANC', 'Cancelada'),
        ('PDNG', 'Pendiente'),
        ('ERRO', 'Error'),
        ('CREA', 'Creada'),
    ])
    purpose_code = models.CharField(max_length=4, default='GDSV')
    requested_execution_date = models.DateField()
    remittance_information_structured = models.CharField(max_length=10, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=60, blank=True, null=True)

    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(Account, related_name='debtor_account', on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(Account, related_name='creditor_account', on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(FinancialInstitution, on_delete=models.CASCADE)
    payment_identification = models.ForeignKey(PaymentIdentification, on_delete=models.CASCADE)
    instructed_amount = models.ForeignKey(InstructedAmount, on_delete=models.CASCADE)
        
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_status_color(self):
        return {
            'PDNG': 'warning',
            'ACSC': 'success',
            'RJCT': 'danger',
            'CANC': 'secondary',
            'ERRO': 'danger',
        }.get(self.transaction_status, 'dark')

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('estado_transferenciaGPT3', args=[str(self.payment_id)])
    
    def __str__(self):
        return f"Transferencia {self.payment_id}"


class GroupHeader(models.Model):
    message_id = models.CharField(max_length=35)
    number_of_transactions = models.IntegerField()
    control_sum = models.DecimalField(max_digits=12, decimal_places=2)
    initiating_party_name = models.CharField(max_length=70)
    create_date_time = models.DateTimeField()

    def __str__(self):
        return self.message_id


class BulkTransfer(models.Model):
    payment_id = models.CharField(max_length=35, unique=True)
    group_header = models.ForeignKey(GroupHeader, on_delete=models.CASCADE)
    transaction_status = models.CharField(max_length=10, choices=[
        ('RJCT', 'Rechazada'),
        ('RCVD', 'Recibida'),
        ('ACCP', 'Aceptada'),
        ('ACTC', 'Aceptada técnicamente'),
        ('ACSP', 'En proceso'),
        ('ACSC', 'Ejecutada con éxito'),
        ('ACWC', 'Con advertencia'),
        ('ACWP', 'Pendiente de aprobación'),
        ('ACCC', 'Concluida'),
        ('CANC', 'Cancelada'),
        ('PDNG', 'Pendiente')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bulk {self.payment_id}"


class PaymentInformation(models.Model):
    bulk = models.ForeignKey(BulkTransfer, on_delete=models.CASCADE, related_name="payment_informations")
    payment_information_id = models.CharField(max_length=35)
    payment_method = models.CharField(max_length=35)
    batch_booking = models.BooleanField(default=True)
    number_of_transactions = models.IntegerField()
    control_sum = models.DecimalField(max_digits=12, decimal_places=2)
    requested_execution_date = models.DateField()
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debtor_agent = models.ForeignKey(FinancialInstitution, on_delete=models.CASCADE)
    charge_bearer = models.CharField(max_length=35)

    def __str__(self):
        return self.payment_information_id


class CreditTransfersDetails(models.Model):
    payment_information = models.ForeignKey(PaymentInformation, on_delete=models.CASCADE, related_name='credit_transfers')
    payment_identification = models.ForeignKey(PaymentIdentification, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    instructed_amount = models.ForeignKey(InstructedAmount, on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(FinancialInstitution, on_delete=models.CASCADE, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)

    def __str__(self):
        return f"Transfer to {self.creditor.creditor_name} ({self.instructed_amount.amount})"
