TRANSFER_TYPES = [
    ('standard', 'Standard'),
    ('instant', 'Instant'),
]

TYPE_STRATEGIES = [
    ('standard_only', 'Standard Only'),
    ('instant_only', 'Instant Only'),
    ('instant_if_available', 'Instant If Available'),
]

TYPE = [
    ('main', 'main'),
    ('virtual', 'virtual'),
]

STATUS_CHOICES = [
    ('RJCT', 'RJCT'),
    ('RCVD', 'RCVD'),
    ('ACCP', 'ACCP'),
    ('ACTP', 'ACTP'),
    ('ACSP', 'ACSP'),
    ('ACWC', 'ACWC'),
    ('ACWP', 'ACWP'),
    ('ACCC', 'ACCC'),
    ('CANC', 'CANC'),
    ('PDNG', 'PDNG'),
]

DIRECTION_CHOICES = [
    ('debit', 'Debit'),
    ('credit', 'Credit'),
]

SANDBOX_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("COMPLETED", "Completed"),
]

SCHEME_CHOICES = [
    ('b2b', 'B2B'),
    ('core', 'CORE'),
]

COLLECTION_STATUS_CHOICES = [
    ('pending', 'Pendiente'),
    ('scheduled', 'Programada'),
    ('confirmed', 'Confirmada'),
    ('canceled', 'Cancelada'),
    ('failed', 'Fallida'),
]

ACCOUNT_TYPES = [
    ('current_account', 'Current Account'),
    ('ring_fenced_account', 'Ring-Fenced Account'),
    ('settlement_account', 'Settlement Account'),
    ('specially_dedicated_account', 'Specially Dedicated Account'),
    ('trust_account', 'Trust Account'),
    ('meal_voucher_account', 'Meal Voucher Account'),
    ('booster_account', 'Booster Account'),
]

ACCOUNT_STATUS = [
    ('active', 'Active'),
    ('closed', 'Closed'),
]

NAME = [
    ('---', '---'),
    ('MIRYA TRADING CO LTD', 'MIRYA TRADING CO LTD'),
    ('ZAIBATSUS.L.', 'ZAIBATSUS.L.'),
    ('ELIZABETH GARDEN GROUP S.L.', 'ELIZABETH GARDEN GROUP S.L.'),
    ('REVSTAR GLOBAL INTERNATIONAL LTD', 'REVSTAR GLOBAL INTERNATIONAL LTD'),
    ('ECLIPS CORPORATION LTD.', 'ECLIPS CORPORATION LTD.'),
    ('CDG SYSTEM LTD', 'CDG SYSTEM LTD'),
    ('BFP FINANCE SERVICE S.L.', 'BFP FINANCE SERVICE S.L.'),
    ('MOHAMMAD REZA NAJAFI KALASHI', 'MOHAMMAD REZA NAJAFI KALASHI'),
    ('SERVICES ET PUBLICITÉ ONLINE LTD', 'SERVICES ET PUBLICITÉ ONLINE LTD'),
    ('XXX', 'XXX'),

]

IBAN = [
    ('---', '---'),
    ('DE86500700100925993805', 'DE86500700100925993805'),
    ('ES3901821250410201520178', 'ES3901821250410201520178'),
    ('ES7901824036500201650056', 'ES7901824036500201650056'),
    ('GB69BUKB20041558708288', 'GB69BUKB20041558708288'),
    ('GB43HBUK40127669998520', 'GB43HBUK40127669998520'),
    ('DE64202208000053288296', 'DE64202208000053288296'),
    ('ES5868880001643861269006', 'ES5868880001643861269006'),
    ('DE41400501500154813455', 'DE41400501500154813455'),
    ('GB33REVO00996939552283', 'GB33REVO00996939552283'),
    ('XXX', 'XXX'),

]

BIC = [
    ('---', '---'),
    ('DEUTDEFFXXX', 'DEUTDEFFXXX'),
    ('BBVAESMMXXX', 'BBVAESMMXXX'),
    ('BUKBGB22XXX', 'BUKBGB22XXX'),
    ('HBUKGB4BXXX', 'HBUKGB4BXXX'),
    ('SXPYDEHHXXX', 'SXPYDEHHXXX'),
    ('QNTOESB2XXX', 'QNTOESB2XXX'),
    ('WELADED1MST', 'WELADED1MST'),
    ('REVOGB21XXX', 'REVOGB21XXX'),
    ('XXX', 'XXX'),

]

BANK = [
    ('---', '---'),
    ('DEUTSCHE BANK AG', 'DEUTSCHE BANK AG'),
    ('BANCO BILBAO VIZCAYA ARGENTARIA S.A.', 'BANCO BILBAO VIZCAYA ARGENTARIA S.A.'),
    ('BARCLAYS BANK UK PLC', 'BARCLAYS BANK UK PLC'),
    ('HSBC UK BANK PLC', 'HSBC UK BANK PLC'),
    ('BANKING CIRCLE', 'BANKING CIRCLE'),
    ('OLINDA SAS SUCURSAL EN ESPAÑA', 'OLINDA SAS SUCURSAL EN ESPAÑA'),
    ('SPARKASSE MÜNSTERLAND OST', 'SPARKASSE MÜNSTERLAND OST'),
    ('REVOLUT LIMITED', 'REVOLUT LIMITED'),
    ('XXX', 'XXX'),

]



STREETNUMBER = [
    ('---', '---'),
    ('TAUNUSANLAGE 12', 'TAUNUSANLAGE 12'),
    ('CALLE IPARRAGUIRRE 20', 'CALLE IPARRAGUIRRE 20'),
    ('CALLE GENERAL RICARDOS 12 PLANTA 4, PUERTA E', 'CALLE GENERAL RICARDOS 12 PLANTA 4, PUERTA E'),
    ('PAVILION DR BARCLAYCARD HOUSE', 'PAVILION DR BARCLAYCARD HOUSE'),
    ('CENTENARY SQUARE 1', 'CENTENARY SQUARE 1'),
    ('MAXIMILIANSTRASSE 54', 'MAXIMILIANSTRASSE 54'),
    ('PZ CATALUNYA NUM.1', 'PZ CATALUNYA NUM.1'),
    ('WESELER STRABE 230', 'WESELER STRABE 230'),
    ('WESTFERRY CIRCUS 7', 'WESTFERRY CIRCUS 7'),
    ('XXX', 'XXX'),

]


ZIPCODECITY = [
    ('---', '---'),
    ('60325 FRANKFURT', '60325 FRANKFURT'),
    ('48009 BILBAO', '48009 BILBAO'),
    ('28012 MADRID', '28012 MADRID'),
    ('NN4 75G NORTHAMPTON', 'NN4 75G NORTHAMPTON'),
    ('B1 1HQ BIRMINGHAM', 'B1 1HQ BIRMINGHAM'),
    ('80538 MÜNCHEN', '80538 MÜNCHEN'),
    ('08850 GAVA', '08850 GAVA'),
    ('48151 MÜNSTER', '48151 MÜNSTER'),
    ('E14 4HD LONDON', 'E14 4HD LONDON'),
    ('XXX', 'XXX'),

]


COUNTRY = [
    ('--', '--'),
    ('DE', 'Germany'),
    ('ES', 'Spain'),
    ('GB', 'Great Britain'),
    ('UK', 'United Kingdom'),
    ('FR', 'France'),

]


CURRENCYCODE = [
    ('---', '---'),
    ('EUR', 'EUR'),
    ('GBP', 'GBP'),
    ('USD', 'USD'),
    ('JPY', 'JPY'),
]