from decimal import Decimal

from django.core.exceptions import ValidationError
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from core.kenya import (
    format_phone, mpesa_msisdn, normalize_phone, validate_kra_pin,
    validate_mpesa_code, validate_national_id,
)
from patients.forms import PatientForm
from patients.models import Patient


class PhoneNumberTests(TestCase):
    def test_accepts_common_kenyan_formats(self):
        for raw in ['0712345678', '712345678', '254712345678', '+254712345678',
                    '+254 712 345 678', '0712-345-678', '(0712) 345678']:
            self.assertEqual(normalize_phone(raw), '+254712345678', raw)

    def test_new_01xx_range_and_landlines(self):
        self.assertEqual(normalize_phone('0110123456'), '+254110123456')
        self.assertEqual(normalize_phone('020 2345678'), '+254202345678')

    def test_rejects_foreign_or_malformed_numbers(self):
        for raw in ['+8801712345678', '12345', '0812345678', 'abc']:
            with self.assertRaises(ValidationError, msg=raw):
                normalize_phone(raw)

    def test_mpesa_msisdn_requires_mobile(self):
        self.assertEqual(mpesa_msisdn('0722 000 111'), '254722000111')
        with self.assertRaises(ValidationError):
            mpesa_msisdn('020 2345678')

    def test_display_format(self):
        self.assertEqual(format_phone('0712345678'), '+254 712 345 678')


class IdentifierTests(TestCase):
    def test_kra_pin(self):
        validate_kra_pin('A012345678Z')
        validate_kra_pin('P051234567Q')
        for bad in ['A12345678Z', '1234567890A', 'B012345678Z']:
            with self.assertRaises(ValidationError):
                validate_kra_pin(bad)

    def test_national_id(self):
        validate_national_id('12345678')
        with self.assertRaises(ValidationError):
            validate_national_id('12AB5678')

    def test_mpesa_code(self):
        validate_mpesa_code('SJK4H7XY2Q')
        with self.assertRaises(ValidationError):
            validate_mpesa_code('TXN-12345')


class TemplateHelperTests(TestCase):
    def render(self, src, **ctx):
        return Template(src).render(Context(ctx))

    def test_ksh_filter_and_currency_tag_are_builtin(self):
        out = self.render('{{ amount|ksh }}|{{ amount|ksh:0 }}|{% currency %}', amount=Decimal('1234567.5'))
        self.assertEqual(out, 'KSh 1,234,567.50|KSh 1,234,568|KSh')

    def test_ksh_handles_empty(self):
        self.assertEqual(self.render('{{ x|ksh }}', x=None), 'KSh 0.00')

    @override_settings(HOSPITAL_NAME='Test Hospital Nakuru')
    def test_hospital_tag(self):
        self.assertEqual(self.render('{% hospital "name" %}'), 'Test Hospital Nakuru')


class PatientKenyaFieldsTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user('p1', password='x')
        self.u2 = User.objects.create_user('p2', password='x')
        Patient.objects.create(user=self.u1, id_type='national_id', id_number='12345678', sha_number='SHA0001')

    def form(self, **data):
        base = {'user': self.u2.pk, 'id_type': 'national_id', 'id_number': '87654321'}
        base.update(data)
        return PatientForm(data=base)

    def test_valid_patient(self):
        form = self.form(emergency_contact_phone='0711000222', county='Kisumu')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['emergency_contact_phone'], '+254711000222')

    def test_duplicate_national_id_rejected(self):
        form = self.form(id_number='12345678')
        self.assertFalse(form.is_valid())
        self.assertIn('id_number', form.errors)

    def test_duplicate_sha_rejected(self):
        form = self.form(sha_number='sha0001')
        self.assertFalse(form.is_valid())
        self.assertIn('sha_number', form.errors)

    def test_national_id_format_checked(self):
        form = self.form(id_number='ABC')
        self.assertFalse(form.is_valid())
        self.assertIn('id_number', form.errors)

    def test_passport_allows_letters(self):
        form = self.form(id_type='passport', id_number='ak123456')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['id_number'], 'AK123456')


class RegistrationTests(TestCase):
    def test_self_registration_saves_kenyan_details(self):
        resp = self.client.post(reverse('accounts:register'), {
            'first_name': 'Achieng', 'last_name': 'Otieno', 'email': 'a@example.com',
            'phone': '0712 345 678', 'national_id': '30123456', 'sha_number': 'sha123',
            'username': 'achieng', 'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
            'date_of_birth': '1995-04-01', 'gender': 'Female',
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='achieng')
        self.assertEqual(user.phone, '+254712345678')
        self.assertEqual(user.gender, 'Female')
        self.assertEqual(user.patient_profile.id_number, '30123456')
        self.assertEqual(user.patient_profile.sha_number, 'SHA123')
