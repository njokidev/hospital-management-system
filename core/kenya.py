"""
Kenya-specific reference data, validators and helpers.

Everything that is particular to running MedCare in Kenya lives here so the
rest of the code base can stay country-agnostic: counties, facility levels,
regulatory bodies, phone/ID/KRA PIN validation and M-Pesa formatting.
"""
import re

from django.core.exceptions import ValidationError


# ── Counties (official codes 001–047, Constitution of Kenya 2010, First Schedule)
COUNTIES = [
    ('001', 'Mombasa'), ('002', 'Kwale'), ('003', 'Kilifi'), ('004', 'Tana River'),
    ('005', 'Lamu'), ('006', 'Taita Taveta'), ('007', 'Garissa'), ('008', 'Wajir'),
    ('009', 'Mandera'), ('010', 'Marsabit'), ('011', 'Isiolo'), ('012', 'Meru'),
    ('013', 'Tharaka-Nithi'), ('014', 'Embu'), ('015', 'Kitui'), ('016', 'Machakos'),
    ('017', 'Makueni'), ('018', 'Nyandarua'), ('019', 'Nyeri'), ('020', 'Kirinyaga'),
    ('021', "Murang'a"), ('022', 'Kiambu'), ('023', 'Turkana'), ('024', 'West Pokot'),
    ('025', 'Samburu'), ('026', 'Trans Nzoia'), ('027', 'Uasin Gishu'),
    ('028', 'Elgeyo-Marakwet'), ('029', 'Nandi'), ('030', 'Baringo'), ('031', 'Laikipia'),
    ('032', 'Nakuru'), ('033', 'Narok'), ('034', 'Kajiado'), ('035', 'Kericho'),
    ('036', 'Bomet'), ('037', 'Kakamega'), ('038', 'Vihiga'), ('039', 'Bungoma'),
    ('040', 'Busia'), ('041', 'Siaya'), ('042', 'Kisumu'), ('043', 'Homa Bay'),
    ('044', 'Migori'), ('045', 'Kisii'), ('046', 'Nyamira'), ('047', 'Nairobi'),
]
COUNTY_CHOICES = [(name, name) for _code, name in COUNTIES]

# ── Kenya Essential Package for Health (KEPH) facility levels
KEPH_LEVEL_CHOICES = [
    (1, 'Level 1 – Community'),
    (2, 'Level 2 – Dispensary / Clinic'),
    (3, 'Level 3 – Health Centre / Nursing Home'),
    (4, 'Level 4 – Sub-County / Primary Hospital'),
    (5, 'Level 5 – County Referral Hospital'),
    (6, 'Level 6 – National Referral Hospital'),
]

# ── Patient identification documents
ID_TYPE_CHOICES = [
    ('national_id', 'National ID'),
    ('birth_certificate', 'Birth Certificate (minors)'),
    ('passport', 'Passport'),
    ('alien_id', 'Alien / Foreigner ID'),
    ('refugee_id', 'Refugee ID'),
    ('none', 'Not provided'),
]

# ── Health professional regulators
REGULATORY_BODY_CHOICES = [
    ('KMPDC', 'Kenya Medical Practitioners and Dentists Council'),
    ('COC', 'Clinical Officers Council'),
    ('NCK', 'Nursing Council of Kenya'),
    ('PPB', 'Pharmacy and Poisons Board'),
    ('KMLTTB', 'Kenya Medical Laboratory Technicians and Technologists Board'),
    ('RPB', 'Radiation Protection Board / Society of Radiography'),
    ('KNDI', 'Kenya Nutritionists and Dieticians Institute'),
    ('Other', 'Other'),
]

RELATIONSHIP_CHOICES = [
    ('Spouse', 'Spouse'), ('Parent', 'Parent'), ('Child', 'Child'),
    ('Sibling', 'Sibling'), ('Guardian', 'Guardian'), ('Relative', 'Relative'),
    ('Friend', 'Friend'), ('Other', 'Other'),
]


# ── Phone numbers ──────────────────────────────────────────────────────────
# Kenyan mobile numbers are 07XX XXX XXX or 01XX XXX XXX (new Safaricom/Airtel
# ranges). Landlines are 0[2-6]X... and are accepted in looser form.
_MOBILE_RE = re.compile(r'^(?:\+?254|0)?([17]\d{8})$')
_LANDLINE_RE = re.compile(r'^(?:\+?254|0)([2-6]\d{6,8})$')


def _digits(value):
    return re.sub(r'[\s\-().]', '', str(value or ''))


def normalize_phone(value):
    """Return a Kenyan number in E.164 form (+2547XXXXXXXX) or raise ValidationError.

    Accepts 0712345678, 712345678, 254712345678, +254 712 345 678, 0110 123456,
    and landlines such as 020 2345678.
    """
    raw = _digits(value)
    if not raw:
        return ''
    m = _MOBILE_RE.match(raw)
    if m:
        return f'+254{m.group(1)}'
    m = _LANDLINE_RE.match(raw)
    if m:
        return f'+254{m.group(1)}'
    raise ValidationError(
        'Enter a valid Kenyan phone number, e.g. 0712 345 678 or +254 712 345 678.',
        code='invalid_phone',
    )


def mpesa_msisdn(value):
    """Format a mobile number the way the Daraja API expects: 2547XXXXXXXX."""
    phone = normalize_phone(value)
    if not phone or not _MOBILE_RE.match(phone.lstrip('+')):
        raise ValidationError('Enter a Kenyan mobile number registered for M-Pesa.', code='invalid_msisdn')
    return phone.lstrip('+')


def format_phone(value):
    """Human-friendly display: +254 712 345 678."""
    try:
        p = normalize_phone(value)
    except ValidationError:
        return value
    if len(p) == 13:
        return f'{p[:4]} {p[4:7]} {p[7:10]} {p[10:]}'
    return p


# ── Identity & tax numbers ─────────────────────────────────────────────────
_NATIONAL_ID_RE = re.compile(r'^\d{6,9}$')
_KRA_PIN_RE = re.compile(r'^[AP]\d{9}[A-Z]$')
_MPESA_CODE_RE = re.compile(r'^[A-Z0-9]{10}$')


def validate_national_id(value):
    if value and not _NATIONAL_ID_RE.match(str(value).strip()):
        raise ValidationError('A Kenyan National ID number is 6–9 digits.', code='invalid_national_id')


def validate_kra_pin(value):
    if value and not _KRA_PIN_RE.match(str(value).strip().upper()):
        raise ValidationError('KRA PIN format is a letter (A or P), 9 digits and a letter, e.g. A012345678Z.',
                              code='invalid_kra_pin')


def validate_mpesa_code(value):
    if value and not _MPESA_CODE_RE.match(str(value).strip().upper()):
        raise ValidationError('An M-Pesa transaction code is 10 letters/digits, e.g. SJK4H7XY2Q.',
                              code='invalid_mpesa_code')


def validate_id_document(id_type, id_number):
    """Cross-field validation for patient identification."""
    if id_type == 'none' or not id_type:
        return
    if not id_number:
        raise ValidationError({'id_number': 'Enter the document number for the selected ID type.'})
    if id_type == 'national_id':
        try:
            validate_national_id(id_number)
        except ValidationError as e:
            raise ValidationError({'id_number': e.messages})


class KenyanPhoneFormMixin:
    """Normalise every field listed in ``phone_fields`` to +254 format on clean()."""

    phone_fields = ('phone',)

    def clean(self):
        cleaned = super().clean()
        for name in self.phone_fields:
            if name in self.fields and cleaned.get(name):
                try:
                    cleaned[name] = normalize_phone(cleaned[name])
                except ValidationError as e:
                    self.add_error(name, e)
        return cleaned

    def _add_phone_placeholders(self):
        for name in self.phone_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault('placeholder', '07XX XXX XXX')
