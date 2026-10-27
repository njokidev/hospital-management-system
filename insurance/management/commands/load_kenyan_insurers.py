"""
Load the Social Health Authority (SHA) schemes and common Kenyan private
medical insurers. Safe to run repeatedly — existing records are left as-is.

    python manage.py load_kenyan_insurers
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from insurance.models import InsuranceProvider, InsurancePlan

SHA = {
    'name': 'Social Health Authority (SHA)',
    'contact_person': 'SHA Provider Relations',
    'address': 'Nairobi, Kenya',
    'plans': [
        ('SHIF – Primary Healthcare Fund', 100, 'Level 2–3 outpatient care, covered through the Primary Healthcare Fund. Billed at SHA tariff.'),
        ('SHIF – Social Health Insurance Fund', 100, 'Secondary and tertiary care (inpatient, outpatient, surgery, maternity, dialysis, etc.) at SHA benefit-package tariffs. Patient pays any difference above the tariff.'),
        ('ECCIF – Emergency, Chronic & Critical Illness Fund', 100, 'Emergency care and chronic/critical illness once SHIF limits are exhausted. Billed at SHA tariff.'),
    ],
}

# Private insurers commonly accepted by Kenyan hospitals. Contact details are
# left for the hospital to fill in from its own provider agreements.
PRIVATE = [
    'AAR Insurance Kenya', 'APA Insurance', 'Britam', 'CIC Insurance Group',
    'First Assurance', 'GA Insurance', 'Jubilee Health Insurance',
    'Madison General Insurance', 'Old Mutual Kenya', 'Pacis Insurance',
]


class Command(BaseCommand):
    help = 'Create SHA schemes and common Kenyan private medical insurers.'

    def handle(self, *args, **options):
        created = 0
        sha, new = InsuranceProvider.objects.get_or_create(
            name=SHA['name'],
            defaults={'contact_person': SHA['contact_person'], 'phone': '', 'address': SHA['address']},
        )
        created += new
        for name, pct, desc in SHA['plans']:
            _, new = InsurancePlan.objects.get_or_create(
                provider=sha, name=name,
                defaults={'coverage_percentage': pct, 'max_coverage': Decimal('0'), 'description': desc},
            )
            created += new

        for name in PRIVATE:
            provider, new = InsuranceProvider.objects.get_or_create(
                name=name, defaults={'contact_person': 'Provider relations', 'phone': ''},
            )
            created += new
            _, new = InsurancePlan.objects.get_or_create(
                provider=provider, name=f'{name} – Corporate Medical',
                defaults={
                    'coverage_percentage': 100,
                    'max_coverage': Decimal('0'),
                    'description': 'Set the inpatient/outpatient limits from the member scheme. 0 = per member benefit card.',
                },
            )
            created += new
        self.stdout.write(self.style.SUCCESS(f'Kenyan insurers loaded ({created} new records).'))
