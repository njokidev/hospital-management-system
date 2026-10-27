"""
Shared Kenyan demo data used by the seed_* management commands.

Everything here is fictional demo data: names are common Kenyan names, phone
numbers are random, and ID / KRA / SHA numbers are generated in the correct
shape but do not belong to anyone.
"""
import random
import string

# ── People ──────────────────────────────────────────────────────────────────
FIRST_NAMES_MALE = [
    'Brian', 'Kevin', 'Dennis', 'Collins', 'Victor', 'Felix', 'Samuel', 'Peter',
    'James', 'John', 'Daniel', 'Joseph', 'Kiprop', 'Kibet', 'Otieno', 'Omondi',
    'Mutua', 'Kamau', 'Mwangi', 'Wekesa', 'Hassan', 'Abdi', 'Mohamed', 'Juma',
]
FIRST_NAMES_FEMALE = [
    'Wanjiku', 'Njeri', 'Achieng', 'Atieno', 'Akinyi', 'Chebet', 'Jepkosgei',
    'Nafula', 'Naliaka', 'Wambui', 'Muthoni', 'Mumbua', 'Faith', 'Mercy', 'Grace',
    'Esther', 'Joy', 'Purity', 'Caroline', 'Lilian', 'Amina', 'Fatuma', 'Zawadi', 'Neema',
]
LAST_NAMES = [
    'Kamau', 'Mwangi', 'Njoroge', 'Kariuki', 'Wanjala', 'Otieno', 'Odhiambo',
    'Ochieng', 'Onyango', 'Mutua', 'Musyoka', 'Kiprotich', 'Koech', 'Rotich',
    'Cheruiyot', 'Wekesa', 'Barasa', 'Wafula', 'Mohamed', 'Hassan', 'Ali',
    'Omondi', 'Kimani', 'Gitau', 'Muriuki', 'Ndungu', 'Nyambura', 'Akinyi',
]

# ── Places (Nairobi neighbourhoods and nearby towns) ────────────────────────
NAIROBI_AREAS = [
    'Westlands', 'Kilimani', 'Lavington', 'Karen', 'Kileleshwa', 'Parklands',
    'South B', 'South C', 'Embakasi', 'Kasarani', 'Roysambu', 'Donholm',
    'Buruburu', 'Umoja', 'Langata', 'Ngong Road', 'Kahawa', 'Ruaka',
]
AREA_SUB_COUNTY = {
    'Westlands': 'Westlands', 'Kilimani': 'Dagoretti North', 'Lavington': 'Dagoretti North',
    'Karen': 'Langata', 'Kileleshwa': 'Dagoretti North', 'Parklands': 'Westlands',
    'South B': 'Makadara', 'South C': 'Langata', 'Embakasi': 'Embakasi East',
    'Kasarani': 'Kasarani', 'Roysambu': 'Roysambu', 'Donholm': 'Embakasi West',
    'Buruburu': 'Makadara', 'Umoja': 'Embakasi West', 'Langata': 'Langata',
    'Ngong Road': 'Dagoretti South', 'Kahawa': 'Roysambu', 'Ruaka': 'Kiambaa',
}
STREETS = ['Ngong Rd', 'Waiyaki Way', 'Argwings Kodhek Rd', 'Mombasa Rd', 'Thika Rd',
           'Jogoo Rd', 'Langata Rd', 'Kiambu Rd', 'Lenana Rd', 'Riverside Dr']

HOSPITAL_ADDRESS = 'Upper Hill, Hospital Road, P.O. Box 00000-00100, Nairobi'

# ── Organisations ───────────────────────────────────────────────────────────
# (name, contact person, email)
PHARMA_SUPPLIERS = [
    ('KEMSA (Kenya Medical Supplies Authority)', 'Supply Desk', 'orders@kemsa.example.com'),
    ('MEDS (Mission for Essential Drugs & Supplies)', 'Order Desk', 'orders@meds.example.com'),
    ('Cosmos Ltd', 'Sales Team', 'sales@cosmos.example.com'),
    ('Dawa Life Sciences', 'Sales Team', 'sales@dawa.example.com'),
    ('Universal Corporation Ltd', 'Sales Team', 'sales@ucl.example.com'),
    ('Regal Pharmaceuticals', 'Sales Team', 'sales@regal.example.com'),
]
MANUFACTURERS = ['Cosmos', 'Dawa', 'Universal Corp', 'Regal', 'Beta Healthcare', 'GSK', 'Novartis']

INSURERS = [
    'Social Health Authority (SHA)', 'AAR Insurance Kenya', 'Jubilee Health Insurance',
    'Britam', 'CIC Insurance Group', 'Madison General Insurance', 'APA Insurance',
]

# ── Payments ────────────────────────────────────────────────────────────────
PAYMENT_METHODS = ['M-Pesa', 'M-Pesa', 'M-Pesa', 'Cash', 'Card', 'Bank Transfer', 'SHA', 'Insurance']


def phone():
    return f'+2547{random.randint(10000000, 99999999)}'


def landline():
    return f'+25420{random.randint(2000000, 4999999)}'


def address():
    area = random.choice(NAIROBI_AREAS)
    return f'{random.choice(STREETS)}, {area}, Nairobi'


def residence():
    """(county, sub_county, ward) for a Nairobi-area patient."""
    area = random.choice(NAIROBI_AREAS)
    county = 'Kiambu' if area == 'Ruaka' else 'Nairobi'
    return county, AREA_SUB_COUNTY[area], area


def national_id():
    return str(random.randint(20000000, 39999999))


def kra_pin():
    return f'A{random.randint(0, 999999999):09d}{random.choice(string.ascii_uppercase)}'


def nssf_number():
    return str(random.randint(1000000000, 2999999999))


def sha_number():
    return f'SHA{random.randint(10000000, 99999999)}'


def mpesa_code():
    alphabet = string.ascii_uppercase + string.digits
    return random.choice('STU') + ''.join(random.choice(alphabet) for _ in range(9))


def payment(methods=None):
    """kwargs for a Payment with a reference that matches its method."""
    method = random.choice(methods or PAYMENT_METHODS)
    if method == 'M-Pesa':
        ref = mpesa_code()
    elif method == 'SHA':
        ref = f'SHA-CLM-{random.randint(100000, 999999)}'
    elif method == 'Bank Transfer':
        ref = f'FT{random.randint(10**9, 10**10 - 1)}'
    elif method == 'Card':
        ref = f'POS-{random.randint(100000, 999999)}'
    else:
        ref = ''
    kwargs = {'payment_method': method, 'transaction_id': ref}
    if method == 'M-Pesa':
        kwargs['payer_phone'] = phone()
    return kwargs


def number_plate(i=None):
    """Kenyan private vehicle plate, e.g. KDJ 123A."""
    prefix = 'KD' + random.choice('ABCDEFGHJ')
    return f'{prefix} {random.randint(100, 999)}{random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")}'


# Professional regulator by staff role
REGULATOR_BY_ROLE = {
    'Doctor': 'KMPDC', 'Nurse': 'NCK', 'Pharmacist': 'PPB', 'Lab Technician': 'KMLTTB',
}


def licence_number(body):
    prefix = {'KMPDC': 'A', 'NCK': 'NCK/', 'PPB': 'PPB/P/', 'KMLTTB': 'KMLTTB/'}.get(body, '')
    return f'{prefix}{random.randint(1000, 99999)}'
