import json
import re

class ValidationError(Exception): pass

with open(r'./dbapi-SCT.json', 'r', encoding='utf-8') as f:
    spec = json.load(f)

payload_structure = {
    '/': {
        'post': {
            'parameters': [
                {
                    'name': 'idempotency-id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'otp',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {'name': 'purposeCode', 'schema': {'$ref_name': 'PurposeCode'}},
                {'name': 'requestedExecutionDate', 'schema': {'$ref_name': 'RequestedExecutionDate'}},
                {'name': 'debtor', 'schema': {'$ref_name': 'Debtor'}},
                {'name': 'debtorAccount', 'schema': {'$ref_name': 'DebtorAccount'}},
                {'name': 'paymentIdentification', 'schema': {'$ref_name': 'PaymentIdentification'}},
                {'name': 'instructedAmount', 'schema': {'$ref_name': 'InstructedAmount'}},
                {'name': 'creditorAgent', 'schema': {'$ref_name': 'CreditorAgent'}},
                {'name': 'creditor', 'schema': {'$ref_name': 'Creditor'}},
                {'name': 'creditorAccount', 'schema': {'$ref_name': 'CreditorAccount'}},
                {'name': 'remittanceInformationStructured', 'schema': {'$ref_name': 'RemittanceInformationStructured'}},
                {'name': 'remittanceInformationUnstructured', 'schema': {'$ref_name': 'RemittanceInformationUnstructured'}}
            ]
        }
    },
    '/{paymentId}/status': {
        'get': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        }
    },
    '/{paymentId}': {
        'get': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        },
        'delete': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'idempotency-id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'otp',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        },
        'patch': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'idempotency-id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'otp',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {'name': 'action', 'schema': {'$ref_name': 'Action'}},
                {'name': 'authId', 'schema': {'$ref_name': 'AuthId'}}
            ]
        }
    },
    '/bulk': {
        'post': {
            'parameters': [
                {
                    'name': 'idempotency-id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'otp',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {'name': 'groupHeader', 'schema': {'$ref_name': 'GroupHeader'}},
                {
                    'name': 'paymentInformation',
                    'schema': {
                        'type': 'array',
                        'items': {'$ref': '#/components/schemas/PaymentInformation'}
                    }
                }
            ]
        }
    },
    '/bulk/{paymentId}/status': {
        'get': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        }
    },
    '/bulk/{paymentId}': {
        'get': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        },
        'delete': {
            'parameters': [
                {
                    'name': 'paymentId',
                    'schema': {
                        'in': 'path',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'idempotency-id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': 'uuid',
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'otp',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': None,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                },
                {
                    'name': 'Correlation-Id',
                    'schema': {
                        'in': 'header',
                        'type': 'string',
                        'format': None,
                        'maxLength': 50,
                        'minLength': None,
                        'enum': None,
                        '$ref_name': None
                    }
                }
            ]
        }
    }
}

grouped_by_tag = {'Create Sepa Credit Transfers': {'idempotency-id': {'in': 'header', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'otp': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'Correlation-Id': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': 50, 'minLength': None, 'enum': None, '$ref_name': None}, 'purposeCode': {'$ref_name': 'PurposeCode'}, 'requestedExecutionDate': {'$ref_name': 'RequestedExecutionDate'}, 'debtor': {'$ref_name': 'Debtor'}, 'debtorAccount': {'$ref_name': 'DebtorAccount'}, 'paymentIdentification': {'$ref_name': 'PaymentIdentification'}, 'instructedAmount': {'$ref_name': 'InstructedAmount'}, 'creditorAgent': {'$ref_name': 'CreditorAgent'}, 'creditor': {'$ref_name': 'Creditor'}, 'creditorAccount': {'$ref_name': 'CreditorAccount'}, 'remittanceInformationStructured': {'$ref_name': 'RemittanceInformationStructured'}, 'remittanceInformationUnstructured': {'$ref_name': 'RemittanceInformationUnstructured'}, 'groupHeader': {'$ref_name': 'GroupHeader'}, 'paymentInformation': {'type': 'array', 'items': {'$ref': '#/components/schemas/PaymentInformation'}}}, 'Get status for Sepa Credit Transfers': {'paymentId': {'in': 'path', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'Correlation-Id': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': 50, 'minLength': None, 'enum': None, '$ref_name': None}}, 'Get details for Sepa Credit Transfers': {'paymentId': {'in': 'path', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'Correlation-Id': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': 50, 'minLength': None, 'enum': None, '$ref_name': None}}, 'Cancel Sepa Credit Transfers': {'paymentId': {'in': 'path', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'idempotency-id': {'in': 'header', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'otp': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'Correlation-Id': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': 50, 'minLength': None, 'enum': None, '$ref_name': None}}, 'Second Factor Retry': {'paymentId': {'in': 'path', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'idempotency-id': {'in': 'header', 'type': 'string', 'format': 'uuid', 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'otp': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': None, 'minLength': None, 'enum': None, '$ref_name': None}, 'Correlation-Id': {'in': 'header', 'type': 'string', 'format': None, 'maxLength': 50, 'minLength': None, 'enum': None, '$ref_name': None}, 'action': {'$ref_name': 'Action'}, 'authId': {'$ref_name': 'AuthId'}}}

def validate_PurposeCode(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for PurposeCode')
    return True

def validate_RequestedExecutionDate(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for RequestedExecutionDate')
    return True

def validate_Debtor(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for Debtor')
    if 'debtorName' not in obj:
        raise ValidationError('Missing debtorName in Debtor')
    return True

def validate_DebtorAccount(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for DebtorAccount')
    if 'iban' not in obj:
        raise ValidationError('Missing iban in DebtorAccount')
    return True

def validate_PaymentIdentification(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for PaymentIdentification')
    return True

def validate_InstructedAmount(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for InstructedAmount')
    if 'amount' not in obj:
        raise ValidationError('Missing amount in InstructedAmount')
    if 'currency' not in obj:
        raise ValidationError('Missing currency in InstructedAmount')
    if 'amount' in obj and not isinstance(obj['amount'], (int, float)):
        raise ValidationError('amount must be of type number')
    return True

def validate_CreditorAgent(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for CreditorAgent')
    if 'financialInstitutionId' not in obj:
        raise ValidationError('Missing financialInstitutionId in CreditorAgent')
    return True

def validate_Creditor(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for Creditor')
    if 'creditorName' not in obj:
        raise ValidationError('Missing creditorName in Creditor')
    return True

def validate_CreditorAccount(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for CreditorAccount')
    if 'currency' not in obj:
        raise ValidationError('Missing currency in CreditorAccount')
    if 'iban' not in obj:
        raise ValidationError('Missing iban in CreditorAccount')
    return True

def validate_RemittanceInformationStructured(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for RemittanceInformationStructured')
    return True

def validate_RemittanceInformationUnstructured(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for RemittanceInformationUnstructured')
    return True

def validate_Action(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for Action')
    return True

def validate_AuthId(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for AuthId')
    return True

def validate_GroupHeader(obj):
    if not isinstance(obj, dict):
        raise ValidationError('Expected object for GroupHeader')
    if 'controlSum' not in obj:
        raise ValidationError('Missing controlSum in GroupHeader')
    if 'creationDateTime' not in obj:
        raise ValidationError('Missing creationDateTime in GroupHeader')
    if 'initiatingParty' not in obj:
        raise ValidationError('Missing initiatingParty in GroupHeader')
    if 'messageId' not in obj:
        raise ValidationError('Missing messageId in GroupHeader')
    if 'numberOfTransactions' not in obj:
        raise ValidationError('Missing numberOfTransactions in GroupHeader')
    return True

def validate_Create_Sepa_Credit_Transfers_idempotency_id(value):
    if not isinstance(value, str):
        raise ValidationError('Field idempotency-id must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field idempotency-id max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field idempotency-id min length is None')
    if value not in None:
        raise ValidationError('Field idempotency-id must be one of None')
    return True

def validate_Create_Sepa_Credit_Transfers_otp(value):
    if not isinstance(value, str):
        raise ValidationError('Field otp must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field otp max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field otp min length is None')
    if value not in None:
        raise ValidationError('Field otp must be one of None')
    return True

def validate_Create_Sepa_Credit_Transfers_Correlation_Id(value):
    if not isinstance(value, str):
        raise ValidationError('Field Correlation-Id must be string')
    if hasattr(value, '__len__') and len(value) > 50:
        raise ValidationError('Field Correlation-Id max length is 50')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field Correlation-Id min length is None')
    if value not in None:
        raise ValidationError('Field Correlation-Id must be one of None')
    return True

def validate_Create_Sepa_Credit_Transfers_purposeCode(value):
    return validate_PurposeCode(value)

def validate_Create_Sepa_Credit_Transfers_requestedExecutionDate(value):
    return validate_RequestedExecutionDate(value)

def validate_Create_Sepa_Credit_Transfers_debtor(value):
    return validate_Debtor(value)

def validate_Create_Sepa_Credit_Transfers_debtorAccount(value):
    return validate_DebtorAccount(value)

def validate_Create_Sepa_Credit_Transfers_paymentIdentification(value):
    return validate_PaymentIdentification(value)

def validate_Create_Sepa_Credit_Transfers_instructedAmount(value):
    return validate_InstructedAmount(value)

def validate_Create_Sepa_Credit_Transfers_creditorAgent(value):
    return validate_CreditorAgent(value)

def validate_Create_Sepa_Credit_Transfers_creditor(value):
    return validate_Creditor(value)

def validate_Create_Sepa_Credit_Transfers_creditorAccount(value):
    return validate_CreditorAccount(value)

def validate_Create_Sepa_Credit_Transfers_remittanceInformationStructured(value):
    return validate_RemittanceInformationStructured(value)

def validate_Create_Sepa_Credit_Transfers_remittanceInformationUnstructured(value):
    return validate_RemittanceInformationUnstructured(value)

def validate_Create_Sepa_Credit_Transfers_groupHeader(value):
    return validate_GroupHeader(value)

def validate_Create_Sepa_Credit_Transfers_paymentInformation(value):
    if not isinstance(value, str):
        raise ValidationError('Field paymentInformation must be array')
    return True

def validate_Get_status_for_Sepa_Credit_Transfers_paymentId(value):
    if not isinstance(value, str):
        raise ValidationError('Field paymentId must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field paymentId max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field paymentId min length is None')
    if value not in None:
        raise ValidationError('Field paymentId must be one of None')
    return True

def validate_Get_status_for_Sepa_Credit_Transfers_Correlation_Id(value):
    if not isinstance(value, str):
        raise ValidationError('Field Correlation-Id must be string')
    if hasattr(value, '__len__') and len(value) > 50:
        raise ValidationError('Field Correlation-Id max length is 50')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field Correlation-Id min length is None')
    if value not in None:
        raise ValidationError('Field Correlation-Id must be one of None')
    return True

def validate_Get_details_for_Sepa_Credit_Transfers_paymentId(value):
    if not isinstance(value, str):
        raise ValidationError('Field paymentId must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field paymentId max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field paymentId min length is None')
    if value not in None:
        raise ValidationError('Field paymentId must be one of None')
    return True

def validate_Get_details_for_Sepa_Credit_Transfers_Correlation_Id(value):
    if not isinstance(value, str):
        raise ValidationError('Field Correlation-Id must be string')
    if hasattr(value, '__len__') and len(value) > 50:
        raise ValidationError('Field Correlation-Id max length is 50')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field Correlation-Id min length is None')
    if value not in None:
        raise ValidationError('Field Correlation-Id must be one of None')
    return True

def validate_Cancel_Sepa_Credit_Transfers_paymentId(value):
    if not isinstance(value, str):
        raise ValidationError('Field paymentId must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field paymentId max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field paymentId min length is None')
    if value not in None:
        raise ValidationError('Field paymentId must be one of None')
    return True

def validate_Cancel_Sepa_Credit_Transfers_idempotency_id(value):
    if not isinstance(value, str):
        raise ValidationError('Field idempotency-id must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field idempotency-id max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field idempotency-id min length is None')
    if value not in None:
        raise ValidationError('Field idempotency-id must be one of None')
    return True

def validate_Cancel_Sepa_Credit_Transfers_otp(value):
    if not isinstance(value, str):
        raise ValidationError('Field otp must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field otp max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field otp min length is None')
    if value not in None:
        raise ValidationError('Field otp must be one of None')
    return True

def validate_Cancel_Sepa_Credit_Transfers_Correlation_Id(value):
    if not isinstance(value, str):
        raise ValidationError('Field Correlation-Id must be string')
    if hasattr(value, '__len__') and len(value) > 50:
        raise ValidationError('Field Correlation-Id max length is 50')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field Correlation-Id min length is None')
    if value not in None:
        raise ValidationError('Field Correlation-Id must be one of None')
    return True

def validate_Second_Factor_Retry_paymentId(value):
    if not isinstance(value, str):
        raise ValidationError('Field paymentId must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field paymentId max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field paymentId min length is None')
    if value not in None:
        raise ValidationError('Field paymentId must be one of None')
    return True

def validate_Second_Factor_Retry_idempotency_id(value):
    if not isinstance(value, str):
        raise ValidationError('Field idempotency-id must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field idempotency-id max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field idempotency-id min length is None')
    if value not in None:
        raise ValidationError('Field idempotency-id must be one of None')
    return True

def validate_Second_Factor_Retry_otp(value):
    if not isinstance(value, str):
        raise ValidationError('Field otp must be string')
    if hasattr(value, '__len__') and len(value) > None:
        raise ValidationError('Field otp max length is None')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field otp min length is None')
    if value not in None:
        raise ValidationError('Field otp must be one of None')
    return True

def validate_Second_Factor_Retry_Correlation_Id(value):
    if not isinstance(value, str):
        raise ValidationError('Field Correlation-Id must be string')
    if hasattr(value, '__len__') and len(value) > 50:
        raise ValidationError('Field Correlation-Id max length is 50')
    if hasattr(value, '__len__') and len(value) < None:
        raise ValidationError('Field Correlation-Id min length is None')
    if value not in None:
        raise ValidationError('Field Correlation-Id must be one of None')
    return True

def validate_Second_Factor_Retry_action(value):
    return validate_Action(value)

def validate_Second_Factor_Retry_authId(value):
    return validate_AuthId(value)

def validate_structure_headers_Create_Sepa_Credit_Transfers(headers):
    expected = ['idempotency-id', 'otp', 'Correlation-Id']
    missing = [f for f in expected if f not in headers]
    if missing:
        raise ValidationError(f'Missing headers: {missing}')
    extra = [f for f in headers if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected headers: {extra}')
    return True

def validate_structure_path_Create_Sepa_Credit_Transfers(path_params):
    expected = []
    missing = [f for f in expected if f not in path_params]
    if missing:
        raise ValidationError(f'Missing path params: {missing}')
    extra = [f for f in path_params if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected path params: {extra}')
    return True

def validate_headers_Create_Sepa_Credit_Transfers(headers):
    validate_structure_headers_Create_Sepa_Credit_Transfers(headers)
    validate_Create_Sepa_Credit_Transfers_idempotency_id(headers['idempotency-id'])
    validate_Create_Sepa_Credit_Transfers_otp(headers['otp'])
    validate_Create_Sepa_Credit_Transfers_Correlation_Id(headers['Correlation-Id'])
    return True

def validate_path_Create_Sepa_Credit_Transfers(path_params):
    validate_structure_path_Create_Sepa_Credit_Transfers(path_params)
    return True

def validate_structure_headers_Get_status_for_Sepa_Credit_Transfers(headers):
    expected = ['Correlation-Id']
    missing = [f for f in expected if f not in headers]
    if missing:
        raise ValidationError(f'Missing headers: {missing}')
    extra = [f for f in headers if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected headers: {extra}')
    return True

def validate_structure_path_Get_status_for_Sepa_Credit_Transfers(path_params):
    expected = ['paymentId']
    missing = [f for f in expected if f not in path_params]
    if missing:
        raise ValidationError(f'Missing path params: {missing}')
    extra = [f for f in path_params if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected path params: {extra}')
    return True

def validate_headers_Get_status_for_Sepa_Credit_Transfers(headers):
    validate_structure_headers_Get_status_for_Sepa_Credit_Transfers(headers)
    validate_Get_status_for_Sepa_Credit_Transfers_Correlation_Id(headers['Correlation-Id'])
    return True

def validate_path_Get_status_for_Sepa_Credit_Transfers(path_params):
    validate_structure_path_Get_status_for_Sepa_Credit_Transfers(path_params)
    validate_Get_status_for_Sepa_Credit_Transfers_paymentId(path_params['paymentId'])
    return True

def validate_structure_headers_Get_details_for_Sepa_Credit_Transfers(headers):
    expected = ['Correlation-Id']
    missing = [f for f in expected if f not in headers]
    if missing:
        raise ValidationError(f'Missing headers: {missing}')
    extra = [f for f in headers if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected headers: {extra}')
    return True

def validate_structure_path_Get_details_for_Sepa_Credit_Transfers(path_params):
    expected = ['paymentId']
    missing = [f for f in expected if f not in path_params]
    if missing:
        raise ValidationError(f'Missing path params: {missing}')
    extra = [f for f in path_params if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected path params: {extra}')
    return True

def validate_headers_Get_details_for_Sepa_Credit_Transfers(headers):
    validate_structure_headers_Get_details_for_Sepa_Credit_Transfers(headers)
    validate_Get_details_for_Sepa_Credit_Transfers_Correlation_Id(headers['Correlation-Id'])
    return True

def validate_path_Get_details_for_Sepa_Credit_Transfers(path_params):
    validate_structure_path_Get_details_for_Sepa_Credit_Transfers(path_params)
    validate_Get_details_for_Sepa_Credit_Transfers_paymentId(path_params['paymentId'])
    return True

def validate_structure_headers_Cancel_Sepa_Credit_Transfers(headers):
    expected = ['idempotency-id', 'otp', 'Correlation-Id']
    missing = [f for f in expected if f not in headers]
    if missing:
        raise ValidationError(f'Missing headers: {missing}')
    extra = [f for f in headers if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected headers: {extra}')
    return True

def validate_structure_path_Cancel_Sepa_Credit_Transfers(path_params):
    expected = ['paymentId']
    missing = [f for f in expected if f not in path_params]
    if missing:
        raise ValidationError(f'Missing path params: {missing}')
    extra = [f for f in path_params if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected path params: {extra}')
    return True

def validate_headers_Cancel_Sepa_Credit_Transfers(headers):
    validate_structure_headers_Cancel_Sepa_Credit_Transfers(headers)
    validate_Cancel_Sepa_Credit_Transfers_idempotency_id(headers['idempotency-id'])
    validate_Cancel_Sepa_Credit_Transfers_otp(headers['otp'])
    validate_Cancel_Sepa_Credit_Transfers_Correlation_Id(headers['Correlation-Id'])
    return True

def validate_path_Cancel_Sepa_Credit_Transfers(path_params):
    validate_structure_path_Cancel_Sepa_Credit_Transfers(path_params)
    validate_Cancel_Sepa_Credit_Transfers_paymentId(path_params['paymentId'])
    return True

def validate_structure_headers_Second_Factor_Retry(headers):
    expected = ['idempotency-id', 'otp', 'Correlation-Id']
    missing = [f for f in expected if f not in headers]
    if missing:
        raise ValidationError(f'Missing headers: {missing}')
    extra = [f for f in headers if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected headers: {extra}')
    return True

def validate_structure_path_Second_Factor_Retry(path_params):
    expected = ['paymentId']
    missing = [f for f in expected if f not in path_params]
    if missing:
        raise ValidationError(f'Missing path params: {missing}')
    extra = [f for f in path_params if f not in expected]
    if extra:
        raise ValidationError(f'Unexpected path params: {extra}')
    return True

def validate_headers_Second_Factor_Retry(headers):
    validate_structure_headers_Second_Factor_Retry(headers)
    validate_Second_Factor_Retry_idempotency_id(headers['idempotency-id'])
    validate_Second_Factor_Retry_otp(headers['otp'])
    validate_Second_Factor_Retry_Correlation_Id(headers['Correlation-Id'])
    return True

def validate_path_Second_Factor_Retry(path_params):
    validate_structure_path_Second_Factor_Retry(path_params)
    validate_Second_Factor_Retry_paymentId(path_params['paymentId'])
    return True
