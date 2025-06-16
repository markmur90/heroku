import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
import logging

from django.urls import reverse
from api.core.choices import NAME, IBAN, BIC, BANK, STREETNUMBER, ZIPCODECITY, COUNTRY, CURRENCYCODE, STATUS_CHOICES
logger = logging.getLogger(__name__)


class TransactionStatus(models.TextChoices):
    RJCT = "RJCT", "Rejected"
    RCVD = "RCVD", "Received"
    ACCP = "ACCP", "Accepted"
    ACTC = "ACTC", "Accepted Technical Validation"
    ACSP = "ACSP", "Accepted Settlement in Process"
    ACSC = "ACSC", "Accepted Settlement Completed"
    ACWC = "ACWC", "Accepted with Change"
    ACWP = "ACWP", "Accepted with Pending"
    ACCC = "ACCC", "Accepted Credit Check"
    CANC = "CANC", "Cancelled"
    PDNG = "PDNG", "Pending"


class Action(models.TextChoices):
    """
    Action types for SEPA Credit Transfer transactions.
    """
    CREATE = "CREATE", "Create"
    CANCEL = "CANCEL", "Cancel"
    

class SepaCreditTransferRequest(models.Model):
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    
    transaction_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PDNG")
    purpose_code = models.CharField(max_length=4, blank=True, null=True, default="SEPA")
    
    payment_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    auth_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    
    requested_execution_date = models.DateField(auto_now_add=True ,blank=True, null=True)
    
    debtor_name = models.CharField(max_length=140, choices=NAME, default="MIRYA TRADING CO LTD")
    debtor_adress_street_and_house_number = models.CharField(max_length=70, choices=STREETNUMBER, default="TAUNUSANLAGE 12")
    debtor_adress_zip_code_and_city = models.CharField(max_length=70, choices=ZIPCODECITY, default="60325 FRANKFURT")
    debtor_adress_country = models.CharField(max_length=2, choices=COUNTRY, default="DE")
    debtor_account_iban = models.CharField(max_length=34, choices=IBAN, default="DE86500700100925993805")
    debtor_account_bic = models.CharField(max_length=11, choices=BIC, default="DEUTDEFFXXX")
    debtor_account_currency = models.CharField(max_length=3, choices=CURRENCYCODE, default="EUR")
    
    payment_identification_end_to_end_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    payment_identification_instruction_id = models.CharField(max_length=35, blank=True, null=True)
        
    instructed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    instructed_currency = models.CharField(max_length=3, choices=CURRENCYCODE)
        
    creditor_name = models.CharField(max_length=70, choices=NAME, default="")
    creditor_adress_street_and_house_number = models.CharField(max_length=70, choices=STREETNUMBER, default="")
    creditor_adress_zip_code_and_city = models.CharField(max_length=70, choices=ZIPCODECITY, default="")
    creditor_adress_country = models.CharField(max_length=2, choices=COUNTRY, default="")    
    creditor_account_iban = models.CharField(max_length=34, choices=IBAN, default="")
    creditor_account_bic = models.CharField(max_length=11, choices=BIC, default="")
    creditor_account_currency = models.CharField(max_length=3, choices=CURRENCYCODE, default="")
    creditor_agent_financial_institution_id = models.CharField(max_length=255, choices=BANK, default="")
    
    remittance_information_structured = models.CharField(max_length=10, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return str(self.idempotency_key)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Request"
        verbose_name_plural = "SEPA Credit Transfer Requests"


@receiver(pre_save, sender=SepaCreditTransferRequest)
def set_default_fields(sender, instance, **kwargs):
    try:
        if not instance.payment_identification_end_to_end_id:
            instance.payment_identification_end_to_end_id = uuid.uuid4()
        if not instance.idempotency_key:
            instance.idempotency_key = uuid.uuid4()
        if not instance.payment_id:
            instance.payment_id = uuid.uuid4()
        if not instance.auth_id:
            instance.auth_id = uuid.uuid4()
        logger.info(f"Campos predeterminados establecidos para la transferencia {instance.id}")
    except Exception as e:
        logger.error(f"Error al establecer campos predeterminados: {str(e)}", exc_info=True)
        raise


class SepaCreditTransferUpdateScaRequest(models.Model):
    action = models.CharField(max_length=10, choices=Action.choices)
    auth_id = models.UUIDField()
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Update SCA Request"
        verbose_name_plural = "SEPA Credit Transfer Update SCA Requests"


class SepaCreditTransferResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    auth_id = models.UUIDField()
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Response"
        verbose_name_plural = "SEPA Credit Transfer Responses"


class SepaCreditTransferDetailsResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)
    
    debtor_name = models.CharField(max_length=140)
    debtor_adress_street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    debtor_adress_zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)
    debtor_adress_country = models.CharField(max_length=2)    
    debtor_account_iban = models.CharField(max_length=34)
    debtor_account_bic = models.CharField(max_length=11)
    debtor_account_currency = models.CharField(max_length=3)
    
    creditor_name = models.CharField(max_length=70)
    creditor_adress_street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    creditor_adress_zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)
    creditor_adress_country = models.CharField(max_length=2)    
    creditor_account_iban = models.CharField(max_length=34)
    creditor_account_bic = models.CharField(max_length=11)
    creditor_account_currency = models.CharField(max_length=3)  # Corregido de "creditot_account_currency"
    creditor_agent_financial_institution_id = models.CharField(max_length=255)
    
    payment_identification_end_to_end_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    payment_identification_instruction_id = models.CharField(max_length=35, blank=True, null=True)
        
    instructed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    instructed_currency = models.CharField(max_length=3)
        
    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Details Response"
        verbose_name_plural = "SEPA Credit Transfer Details Responses"


# class ErrorResponse(models.Model):
#     code = models.IntegerField()
#     message = models.CharField(max_length=170, blank=True, null=True)
#     message_id = models.CharField(max_length=255, blank=True, null=True)
    
#     def __str__(self):
#         return f"{self.code} - {self.message_id} - {self.message}"
    
#     class Meta:
#         verbose_name = "Error Response"
#         verbose_name_plural = "Error Responses"



class CategoryPurpose(models.Model):
    code = models.CharField(max_length=4, help_text="Category purpose code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Category Purpose"
        verbose_name_plural = "Category Purposes"


class ServiceLevel(models.Model):
    code = models.CharField(max_length=4, help_text="Service level code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Service Level"
        verbose_name_plural = "Service Levels"


class LocalInstrument(models.Model):
    code = models.CharField(max_length=4, help_text="Local instrument code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Local Instrument"
        verbose_name_plural = "Local Instruments"


from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator

# Validadores comunes
iban_validator = RegexValidator(regex='^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$',message='Formato IBAN inválido')

currency_validator = RegexValidator(regex='^[A-Z]{3}$',message='Código de moneda ISO 4217 inválido')

class Address(models.Model):
    country = models.CharField(max_length=2,validators=[MinLengthValidator(2), MaxLengthValidator(2)],help_text="Código de país ISO 3166-1 alpha-2")
    street_and_house_number = models.CharField(max_length=70,blank=True,help_text="Calle y número")
    zip_code_and_city = models.CharField(max_length=70,blank=True,help_text="Código postal y ciudad")
    
    def __str__(self):
        return f"{self.country} - {self.street_and_house_number} - {self.zip_code_and_city}"
    
    class Meta:
        verbose_name_plural = "Addresses"

class Debtor(models.Model):
    debtor_name = models.CharField(max_length=140)
    debtor_postal_address = models.ForeignKey(Address,on_delete=models.CASCADE,null=True,blank=True)
    
    def __str__(self):
        return f"{self.debtor_name}"

class Creditor(models.Model):
    creditor_name = models.CharField(max_length=70)
    creditor_postal_address = models.ForeignKey(Address,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"{self.creditor_name}"    

class Account(models.Model):
    iban = models.CharField(max_length=34,validators=[iban_validator],help_text="Número de cuenta IBAN")
    currency = models.CharField(max_length=3,validators=[currency_validator],help_text="Código de moneda ISO 4217")

    def __str__(self):
        return f"{self.iban} - {self.currency}"

class PaymentIdentification(models.Model):
    end_to_end_id = models.CharField(max_length=36)
    instruction_id = models.CharField(max_length=36)

    def __str__(self):
        return f"EtEid {self.end_to_end_id} - InstId {self.instruction_id}"

    # def save(self, *args, **kwargs):
    #     # Convertir UUID a cadena antes de truncar
    #     if isinstance(self.end_to_end_id, uuid.UUID):
    #         self.end_to_end_id = str(self.end_to_end_id)[:36]
    #     if isinstance(self.instruction_id, uuid.UUID):
    #         self.instruction_id = str(self.instruction_id)[:36]
    #     super().save(*args, **kwargs)


class InstructedAmount(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3,validators=[currency_validator])

    def __str__(self):
        return f"{self.currency} - {self.amount}"

class CreditorAgent(models.Model):
    financial_institution_id = models.CharField(max_length=35)

    def __str__(self):
        return f"{self.financial_institution_id}"

class SepaCreditTransfer(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('RJCT', 'Rejected'),
        ('RCVD', 'Received'),
        ('ACCP', 'Accepted'),
        ('ACTC', 'AcceptedTechnical'),
        ('ACSP', 'AcceptedSettlement'),
        ('ACSC', 'AcceptedSettlementCompleted'),
        ('ACWC', 'AcceptedWithChange'),
        ('ACWP', 'AcceptedWithoutPosting'),
        ('ACCC', 'AcceptedClearing'),
        ('CANC', 'Cancelled'),
        ('PDNG', 'Pending')
    ]

    # Campos principales
    payment_id = models.UUIDField(unique=True, editable=False)
    auth_id = models.UUIDField(editable=False)
    transaction_status = models.CharField(max_length=4,choices=TRANSACTION_STATUS_CHOICES)
    
    # Relaciones
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='debtor_accounts')
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='creditor_accounts')
    creditor_agent = models.ForeignKey(CreditorAgent, on_delete=models.CASCADE)
    instructed_amount = models.ForeignKey(InstructedAmount, on_delete=models.CASCADE)
    # payment_identification = models.ForeignKey(PaymentIdentification,on_delete=models.SET_NULL,null=True,blank=True)
    end_to_end_id = models.CharField(max_length=36,validators=[MinLengthValidator(36), MaxLengthValidator(36)],blank=True)
    instruction_id = models.CharField(max_length=36,validators=[MinLengthValidator(36), MaxLengthValidator(36)],blank=True)
    
    # Campos opcionales
    purpose_code = models.CharField(max_length=4,validators=[MinLengthValidator(4), MaxLengthValidator(4)],blank=True)
    requested_execution_date = models.DateField(null=True, blank=True)
    remittance_information_structured = models.CharField(max_length=140, blank=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SEPA Credit Transfer"
        verbose_name_plural = "SEPA Credit Transfers"
        
    def get_status_color(self):
        """Devuelve clase CSS según estado"""
        status_colors = {
            'RJCT': 'danger',
            'RCVD': 'info',
            'ACCP': 'success',
            'PDNG': 'warning',
            'CANC': 'secondary'
        }
        return status_colors.get(self.transaction_status, 'light')
    
    def get_absolute_url(self):
        return reverse('check_status2', args=[str(self.payment_id)])
    
    
class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.CharField(max_length=255)
    message_id = models.CharField(max_length=36, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Error {self.code}: {self.message}"
    
