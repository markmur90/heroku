# api/gpt3/schemas.py

sepa_credit_transfer_schema = {
    "type": "object",
    "properties": {
        "purposeCode": {
            "type": "string",
            "maxLength": 4
        },
        "requestedExecutionDate": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "debtor": {
            "type": "object",
            "properties": {
                "debtorName": {
                    "type": "string",
                    "maxLength": 140
                },
                "debtorPostalAddress": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "pattern": "^[A-Z]{2}$"
                        },
                        "addressLine": {
                            "type": "object",
                            "properties": {
                                "streetAndHouseNumber": {
                                    "type": "string",
                                    "maxLength": 70
                                },
                                "zipCodeAndCity": {
                                    "type": "string",
                                    "maxLength": 70
                                }
                            },
                            "required": ["streetAndHouseNumber", "zipCodeAndCity"]
                        }
                    },
                    "required": ["country", "addressLine"]
                }
            },
            "required": ["debtorName"]
        },
        "debtorAccount": {
            "type": "object",
            "properties": {
                "iban": {
                    "type": "string",
                    "pattern": "^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$"
                },
                "currency": {
                    "type": "string",
                    "pattern": "^[A-Z]{3}$"
                }
            },
            "required": ["iban"]
        },
        "paymentIdentification": {
            "type": "object",
            "properties": {
                "endToEndIdentification": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9.-]{1,35}$"
                },
                "instructionId": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9.-]{1,35}$"
                }
            }
        },
        "instructedAmount": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number"
                },
                "currency": {
                    "type": "string",
                    "pattern": "^[A-Z]{3}$"
                }
            },
            "required": ["amount", "currency"]
        },
        "creditorAgent": {
            "type": "object",
            "properties": {
                "financialInstitutionId": {
                    "type": "string"
                }
            },
            "required": ["financialInstitutionId"]
        },
        "creditor": {
            "type": "object",
            "properties": {
                "creditorName": {
                    "type": "string",
                    "maxLength": 70
                },
                "creditorPostalAddress": {
                    "type": "object",
                    "properties": {
                        "country": {
                            "type": "string",
                            "pattern": "^[A-Z]{2}$"
                        },
                        "addressLine": {
                            "type": "object",
                            "properties": {
                                "streetAndHouseNumber": {
                                    "type": "string",
                                    "maxLength": 70
                                },
                                "zipCodeAndCity": {
                                    "type": "string",
                                    "maxLength": 70
                                }
                            },
                            "required": ["streetAndHouseNumber", "zipCodeAndCity"]
                        }
                    },
                    "required": ["country", "addressLine"]
                }
            },
            "required": ["creditorName"]
        },
        "creditorAccount": {
            "type": "object",
            "properties": {
                "iban": {
                    "type": "string",
                    "pattern": "^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$"
                },
                "currency": {
                    "type": "string",
                    "pattern": "^[A-Z]{3}$"
                }
            },
            "required": ["iban", "currency"]
        },
        "remittanceInformationStructured": {
            "type": "string",
            "maxLength": 140
        },
        "remittanceInformationUnstructured": {
            "type": "string",
            "maxLength": 140
        }
    },
    "required": [
        "creditor",
        "creditorAccount",
        "creditorAgent",
        "debtor",
        "debtorAccount",
        "instructedAmount"
    ]
}
