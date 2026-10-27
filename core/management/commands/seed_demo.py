import random
from decimal import Decimal
from datetime import timedelta, date, time

from django.core.management.base import BaseCommand

from core import seed_kenya as ke
from django.utils import timezone
from django.db import transaction

from accounts.models import User, Role
from hospitals.models import Branch
from departments.models import Department, Specialization
from employees.models import Employee
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient
from appointments.models import Appointment, Visit
from pharmacy.models import MedicineCategory, Supplier, Medicine, Prescription, PrescriptionItem
from laboratory.models import LabTest, LabOrder, LabOrderItem, LabResult
from billing.models import Invoice, InvoiceItem, Payment
from insurance.models import InsuranceProvider, InsurancePlan


# ─── Name Data ───────────────────────────────────────────────────────────────

KENYAN_FIRST_NAMES_MALE = [
    'Gitonga', 'Abdi', 'Wekesa', 'Juma', 'Kioko', 'Patrick', 'Omar', 'George',
    'Simiyu', 'Hamisi', 'Makokha', 'Mutiso', 'Otieno', 'Samuel', 'Mwangi', 'Daniel',
    'Brian', 'Muli', 'Ouma', 'Bakari', 'Okoth', 'Kevin', 'Felix', 'James',
    'John', 'Joseph', 'Kiprop', 'Kibet', 'Mutua', 'Kamau', 'Kipchoge', 'Kiptoo',
]

KENYAN_FIRST_NAMES_FEMALE = [
    'Jepkosgei', 'Wangari', 'Amina', 'Eric', 'Esther', 'Anyango', 'Mumbua',
    'Nyokabi', 'Adhiambo', 'Njeri', 'Chebet', 'Nafula', 'Wambui',
    'Muthoni', 'Mercy', 'Grace', 'Joy', 'Lilian', 'Neema', 'Wairimu',
    'Moraa', 'Kerubo', 'Chepkoech', 'Makena', 'Kagendo', 'Mwende', 'Ndanu',
]

KENYAN_LAST_NAMES = [
    'Abdullahi', 'Omondi', 'Kimani', 'Ndungu', 'Kiprotich', 'Kiplagat', 'Ali',
    'Maina', 'Ochieng', 'Keter', 'Kirui', 'Macharia', 'Koech', 'Mutua',
    'Ruto', 'Kariuki', 'Odhiambo', 'Wekesa', 'Musyoka', 'Gathoni',
    'Wambua', 'Langat', 'Paul', 'Cheruiyot', 'Rotich', 'Otieno', 'Njenga',
]

ENGLISH_FIRST_NAMES_MALE = [
    'James', 'John', 'David', 'Michael', 'Robert', 'William', 'Richard',
    'Thomas', 'Daniel', 'Andrew', 'Christopher', 'Matthew', 'Anthony',
    'Mark', 'Steven', 'Paul', 'Peter', 'Brian', 'Kevin', 'Jason',
]

ENGLISH_FIRST_NAMES_FEMALE = [
    'Mary', 'Sarah', 'Emma', 'Olivia', 'Sophia', 'Isabella', 'Mia',
    'Charlotte', 'Amelia', 'Harper', 'Evelyn', 'Abigail', 'Emily',
    'Elizabeth', 'Sofia', 'Chloe', 'Grace', 'Nora', 'Hannah', 'Lily',
]

ALLERGIES = [
    'Penicillin', 'Aspirin', 'Ibuprofen', 'Dust', 'Pollen', 'Peanuts',
    'Shellfish', 'Eggs', 'Milk', 'Soy', 'Wheat', 'None',
]

MEDICAL_HISTORIES = [
    'No significant history', 'Hypertension', 'Diabetes Type 2',
    'Asthma', 'Heart Disease', 'Thyroid Disorder', 'Arthritis',
    'Chronic Kidney Disease', 'Anemia', 'Allergic Rhinitis',
    'Gastroesophageal Reflux', 'Migraine',
]

DIAGNOSES = [
    'Common Cold', 'Influenza', 'Hypertension', 'Type 2 Diabetes',
    'Bronchitis', 'Gastritis', 'Migraine', 'Lower Back Pain',
    'Allergic Rhinitis', 'Pharyngitis', 'Urinary Tract Infection',
    'Pneumonia', 'Dermatitis', 'Anemia', 'Hypothyroidism',
    'Osteoarthritis', 'Asthma', 'Sinusitis', 'Conjunctivitis',
    'Typhoid',
]

SYMPTOMS = [
    'Fever, cough, sore throat', 'Headache, nausea', 'Chest pain, shortness of breath',
    'Abdominal pain, bloating', 'Joint pain, swelling', 'Fatigue, weakness',
    'Dizziness, lightheadedness', 'Skin rash, itching', 'Runny nose, sneezing',
    'Back pain, stiffness', 'Frequent urination', 'Weight loss, loss of appetite',
    'Blurred vision', 'Numbness, tingling', 'Difficulty sleeping',
]

APPOINTMENT_REASONS = [
    'Routine checkup', 'Follow-up visit', 'Persistent headache',
    'Chest pain', 'Stomach ache', 'Fever and cough', 'Back pain',
    'Skin rash', 'Eye irritation', 'Ear pain', 'Joint pain',
    'Breathing difficulty', 'Weight management', 'Diabetes management',
    'Blood pressure check', 'Vaccination', 'Lab result review',
]

DOCTOR_NOTES = [
    'Patient is responding well to treatment.', 'Continue current medication.',
    'Recommended further tests.', 'Advised rest and fluids.',
    'Follow up in 2 weeks.', 'Referred to specialist.',
    'Patient condition is stable.', 'Prescribed antibiotics for 5 days.',
    'Advised dietary changes.', 'Monitor blood pressure daily.',
]

FREQUENCIES = ['Once Daily', 'Twice Daily', 'Three Times Daily', 'Every 8 Hours', 'As Needed', 'Before Bed']
DURATIONS = ['3 days', '5 days', '7 days', '10 days', '14 days', '30 days']
DOSAGES = ['500mg', '250mg', '100mg', '10mg', '5mg', '1 tablet', '2 tablets', '1 spoonful']

TIME_SLOTS = [
    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
    time(11, 0), time(11, 30), time(12, 0),
    time(14, 0), time(14, 30), time(15, 0), time(15, 30),
    time(16, 0), time(16, 30),
]


class Command(BaseCommand):
    help = 'Seed the database with realistic demo data for Hospital Management System'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counts = {}

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing demo data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self._clear_data()

        self.stdout.write(self.style.HTTP_INFO('\n=== Seeding Hospital Management System Demo Data ===\n'))

        with transaction.atomic():
            self._create_roles()
            self._create_super_admin()
            self._create_hospital_admin()
            self._create_hospital_and_branch()
            self._create_departments()
            self._create_specializations()
            self._create_medicine_data()
            self._create_insurance_data()
            self._create_doctors()
            self._create_staff()
            self._create_patients()
            self._create_appointments()
            self._create_prescriptions()
            self._create_lab_orders()
            self._create_invoices()

        self._print_summary()

    def _clear_data(self):
        Payment.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        LabResult.objects.all().delete()
        LabOrderItem.objects.all().delete()
        LabOrder.objects.all().delete()
        PrescriptionItem.objects.all().delete()
        Prescription.objects.all().delete()
        Visit.objects.all().delete()
        Appointment.objects.all().delete()
        DoctorSchedule.objects.all().delete()
        Doctor.objects.all().delete()
        Employee.objects.all().delete()
        Patient.objects.all().delete()
        Specialization.objects.all().delete()
        Department.objects.all().delete()
        Branch.objects.all().delete()
        Medicine.objects.all().delete()
        MedicineCategory.objects.all().delete()
        Supplier.objects.all().delete()
        InsurancePlan.objects.all().delete()
        InsuranceProvider.objects.all().delete()
        Role.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Data cleared.'))

    # ── 1. Roles ─────────────────────────────────────────────────────────

    def _create_roles(self):
        self.stdout.write('Creating roles...')
        role_names = [
            'Super Admin', 'Hospital Admin', 'Doctor', 'Nurse',
            'Receptionist', 'Pharmacist', 'Lab Technician',
            'Accountant', 'HR Manager', 'Patient',
        ]
        for name in role_names:
            Role.objects.get_or_create(name=name)
        self.counts['roles'] = len(role_names)
        self.stdout.write(self.style.SUCCESS(f'  Created {len(role_names)} roles'))

    # ── 2. Super Admin ───────────────────────────────────────────────────

    def _create_super_admin(self):
        self.stdout.write('Creating super admin...')
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@medcare.co.ke',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                phone='+254712345678',
                gender='Male',
                address='MEDCARE Hospital, Nairobi, Kenya',
            )
        else:
            admin = User.objects.get(username='admin')
        role = Role.objects.get(name='Super Admin')
        admin.roles.add(role)
        self.counts['super_admin'] = 1
        self.stdout.write(self.style.SUCCESS('  Super admin created (admin / admin123)'))

    # ── 3. Hospital Admin ────────────────────────────────────────────────

    def _create_hospital_admin(self):
        self.stdout.write('Creating hospital admin...')
        if not User.objects.filter(username='hospitaladmin').exists():
            ha = User.objects.create_user(
                username='hospitaladmin',
                email='hospitaladmin@medcare.co.ke',
                password='admin123',
                first_name='Hospital',
                last_name='Administrator',
                phone='+254712345679',
                gender='Male',
                address='MEDCARE Hospital, Nairobi, Kenya',
            )
        else:
            ha = User.objects.get(username='hospitaladmin')
        role = Role.objects.get(name='Hospital Admin')
        ha.roles.add(role)
        self.counts['hospital_admin'] = 1
        self.stdout.write(self.style.SUCCESS('  Hospital admin created (hospitaladmin / admin123)'))

    # ── 4. Branch ─────────────────────────────────────────────────────

    def _create_hospital_and_branch(self):
        self.stdout.write('Creating branch...')

        branch, _ = Branch.objects.get_or_create(
            name='Nairobi Main Branch',
            defaults={
                'address': '123 Medical Avenue, Kasarani, Nairobi, Kenya',
                'phone': '+254787123456',
                'is_main_branch': True,
                'is_active': True,
            },
        )
        self.branch = branch
        self.counts['branches'] = 1
        self.stdout.write(self.style.SUCCESS('  Main branch created'))

    # ── 5. Departments ───────────────────────────────────────────────────

    def _create_departments(self):
        self.stdout.write('Creating departments...')
        departments_data = [
            ('Cardiology', 'Heart and cardiovascular system care'),
            ('Neurology', 'Brain and nervous system care'),
            ('Pediatrics', 'Medical care for infants, children, and adolescents'),
            ('Orthopedics', 'Musculoskeletal system care'),
            ('Dermatology', 'Skin, hair, and nail care'),
            ('ENT', 'Ear, nose, and throat care'),
            ('Oncology', 'Cancer diagnosis and treatment'),
            ('Gynecology', 'Female reproductive system care'),
            ('Radiology', 'Medical imaging and diagnostics'),
            ('Pathology', 'Laboratory testing and disease diagnosis'),
            ('Emergency Medicine', 'Emergency and critical care'),
        ]
        self.departments = {}
        for name, desc in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                branch=self.branch,
                defaults={
                    'description': desc,
                    'phone': ke.landline(),
                    'email': f'{name.lower().replace(" ", "")}@medcare.co.ke',
                    'is_active': True,
                },
            )
            self.departments[name] = dept
        self.counts['departments'] = len(departments_data)
        self.stdout.write(self.style.SUCCESS(f'  Created {len(departments_data)} departments'))

    # ── 6. Specializations ───────────────────────────────────────────────

    def _create_specializations(self):
        self.stdout.write('Creating specializations...')
        specs_data = {
            'Cardiology': ['Interventional Cardiology', 'Electrophysiology', 'Cardiac Surgery'],
            'Neurology': ['Stroke Medicine', 'Epilepsy', 'Neuromuscular Medicine'],
            'Pediatrics': ['Neonatology', 'Pediatric Surgery', 'Child Development'],
            'Orthopedics': ['Spine Surgery', 'Sports Medicine', 'Joint Replacement'],
            'Dermatology': ['Cosmetic Dermatology', 'Pediatric Dermatology'],
            'ENT': ['Head and Neck Surgery', 'Audiology'],
            'Oncology': ['Medical Oncology', 'Radiation Oncology', 'Surgical Oncology'],
            'Gynecology': ['Obstetrics', 'Reproductive Endocrinology'],
            'Radiology': ['Interventional Radiology', 'MRI', 'CT Scan'],
            'Pathology': ['Clinical Pathology', 'Histopathology'],
            'Emergency Medicine': ['Trauma Care', 'Critical Care'],
        }
        self.specializations = {}
        for dept_name, spec_list in specs_data.items():
            dept = self.departments[dept_name]
            for spec_name in spec_list:
                spec, _ = Specialization.objects.get_or_create(
                    name=spec_name,
                    department=dept,
                    defaults={'description': f'{spec_name} specialization under {dept_name}'},
                )
                self.specializations[spec_name] = spec
        self.counts['specializations'] = len(self.specializations)
        self.stdout.write(self.style.SUCCESS(f'  Created {len(self.specializations)} specializations'))

    # ── 7. Medicine Data ─────────────────────────────────────────────────

    def _create_medicine_data(self):
        self.stdout.write('Creating medicine data...')

        categories_data = [
            ('Analgesics', 'Pain relief medications'),
            ('Antibiotics', 'Antibacterial medications'),
            ('Antihistamines', 'Allergy medications'),
            ('Antidiabetics', 'Diabetes medications'),
            ('Cardiovascular', 'Heart and blood vessel medications'),
            ('Gastrointestinal', 'Digestive system medications'),
            ('Respiratory', 'Respiratory system medications'),
            ('Dermatological', 'Skin care medications'),
            ('Vitamins & Supplements', 'Nutritional supplements'),
            ('Hormones', 'Hormonal medications'),
        ]
        self.med_categories = {}
        for name, desc in categories_data:
            cat, _ = MedicineCategory.objects.get_or_create(name=name, defaults={'description': desc})
            self.med_categories[name] = cat

        suppliers_data = [
            ('Cosmos Ltd', 'Mwangi', '+254711111111', 'sales@supplier.example.com'),
            ('Dawa Life Sciences', 'Rashid', '+254722222222', 'sales@supplier.example.com'),
            ('Universal Corporation Ltd', 'Muriuki', '+254733333333', 'sales@supplier.example.com'),
            ('Regal Pharmaceuticals', 'Barasa', '+254744444444', 'sales@supplier.example.com'),
            ('Beta Healthcare', 'Wanjala', '+254755555555', 'sales@supplier.example.com'),
        ]
        suppliers = []
        for name, contact, phone, email in suppliers_data:
            sup, _ = Supplier.objects.get_or_create(
                name=name,
                defaults={'contact_person': contact, 'phone': phone, 'email': email, 'address': 'Nairobi, Kenya'},
            )
            suppliers.append(sup)

        medicines_data = [
            ('Panadol 500mg', 'Paracetamol', 'Tablet', 'Analgesics', 'Cosmos', 1.50, 500),
            ('Panadol Extra', 'Paracetamol+ caffeine', 'Tablet', 'Analgesics', 'Cosmos', 3.00, 300),
            ('Levocetirizine 5mg', 'Levocetirizine', 'Tablet', 'Antihistamines', 'Cosmos', 5.00, 200),
            ('Azithromycin 500mg', 'Azithromycin', 'Tablet', 'Antibiotics', 'Dawa', 12.00, 150),
            ('Amoxicillin 500mg', 'Amoxicillin', 'Capsule', 'Antibiotics', 'Cosmos', 8.00, 250),
            ('Metformin 500mg', 'Metformin', 'Tablet', 'Antidiabetics', 'Dawa', 4.00, 400),
            ('Amlodipine 5mg', 'Amlodipine', 'Tablet', 'Cardiovascular', 'Universal Corp', 6.00, 300),
            ('Atorvastatin 20mg', 'Atorvastatin', 'Tablet', 'Cardiovascular', 'Regal', 10.00, 200),
            ('Omeprazole 20mg', 'Omeprazole', 'Capsule', 'Gastrointestinal', 'Cosmos', 7.00, 350),
            ('Pantoprazole 40mg', 'Pantoprazole', 'Tablet', 'Gastrointestinal', 'Universal Corp', 8.00, 250),
            ('Salbutamol Inhaler', 'Salbutamol', 'Inhaler', 'Respiratory', 'Dawa', 150.00, 100),
            ('Montelukast 10mg', 'Montelukast', 'Tablet', 'Respiratory', 'Regal', 9.00, 200),
            ('Betnovate Cream', 'Betamethasone', 'Ointment', 'Dermatological', 'GSK', 25.00, 150),
            ('Fusidic Cream', 'Fusidic Acid', 'Ointment', 'Dermatological', 'Cosmos', 30.00, 120),
            ('Calpol 500mg', 'Paracetamol', 'Syrup', 'Analgesics', 'GSK', 35.00, 200),
            ('Vitamin C 500mg', 'Ascorbic Acid', 'Tablet', 'Vitamins & Supplements', 'Regal', 2.00, 500),
            ('Calcium + Vitamin D3', 'Calcium+Vitamin D3', 'Tablet', 'Vitamins & Supplements', 'Universal Corp', 5.00, 400),
            ('Eltroxin 50mcg', 'Levothyroxine', 'Tablet', 'Hormones', 'Cosmos', 15.00, 200),
            ('Diazepam 5mg', 'Diazepam', 'Tablet', 'Analgesics', 'Dawa', 4.50, 100),
            ('Cetirizine 10mg', 'Cetirizine', 'Tablet', 'Antihistamines', 'Regal', 3.50, 300),
            ('Paracetamol 650mg', 'Paracetamol', 'Tablet', 'Analgesics', 'Micro Labs', 2.00, 450),
            ('Augmentin 625mg', 'Amoxicillin+Clavulanate', 'Tablet', 'Antibiotics', 'GSK', 20.00, 180),
            ('Panadol CF', 'Paracetamol+Phenylephrine', 'Tablet', 'Analgesics', 'GSK', 6.00, 250),
            ('Rizact 10mg', 'Rizatriptan', 'Tablet', 'Analgesics', 'Sun Pharma', 25.00, 80),
            ('Losec 20mg', 'Omeprazole', 'Capsule', 'Gastrointestinal', 'Cosmos', 6.50, 300),
        ]

        today = timezone.now().date()
        self.medicines = []
        for name, generic, cat_choice, cat_fk_name, supplier_name, price, stock in medicines_data:
            med, _ = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'generic_name': generic,
                    'category': cat_choice,
                    'category_fk': self.med_categories.get(cat_fk_name),
                    'manufacturer': supplier_name,
                    'unit_price': price,
                    'stock_quantity': stock,
                    'minimum_stock': 10,
                    'expiry_date': today + timedelta(days=random.randint(180, 730)),
                    'batch_number': f'BATCH-{random.randint(1000, 9999)}',
                    'is_active': True,
                },
            )
            sup_obj = Supplier.objects.filter(name__icontains=supplier_name).first()
            if sup_obj:
                med.suppliers.add(sup_obj)
            self.medicines.append(med)

        self.counts['medicine_categories'] = len(categories_data)
        self.counts['suppliers'] = len(suppliers_data)
        self.counts['medicines'] = len(medicines_data)
        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(categories_data)} categories, {len(suppliers_data)} suppliers, {len(medicines_data)} medicines'
        ))

    # ── 8. Insurance ─────────────────────────────────────────────────────

    def _create_insurance_data(self):
        self.stdout.write('Creating insurance providers and plans...')
        providers_data = [
            ('AAR Insurance Kenya', 'Abdullahi', '+254712345678', 'claims@insurer.example.com'),
            ('Jubilee Health Insurance', 'Kinyua', '+254723456789', 'claims@insurer.example.com'),
            ('Britam', 'Kiprotich', '+254734567890', 'claims@insurer.example.com'),
            ('CIC Insurance Group', 'Ochieng', '+254745678901', 'claims@insurer.example.com'),
        ]
        self.insurance_providers = []
        for name, contact, phone, email in providers_data:
            prov, _ = InsuranceProvider.objects.get_or_create(
                name=name,
                defaults={'contact_person': contact, 'phone': phone, 'email': email, 'address': 'Nairobi, Kenya'},
            )
            self.insurance_providers.append(prov)

        plans_data = [
            ('Prime Basic', 50, 50000, 'Basic health coverage'),
            ('Prime Premium', 75, 200000, 'Premium health coverage with higher limits'),
            ('Jubilee Gold', 80, 300000, 'Gold tier comprehensive coverage'),
            ('Jubilee Silver', 60, 100000, 'Silver tier coverage'),
            ('Reliance Family', 70, 150000, 'Family floater plan'),
            ('Reliance Individual', 65, 100000, 'Individual health plan'),
            ('Eastern Essential', 55, 75000, 'Essential health coverage'),
            ('Eastern Comprehensive', 85, 500000, 'Comprehensive health coverage'),
        ]
        self.insurance_plans = []
        for name, coverage, max_cov, desc in plans_data:
            prov = random.choice(self.insurance_providers)
            plan, _ = InsurancePlan.objects.get_or_create(
                name=name,
                provider=prov,
                defaults={
                    'coverage_percentage': coverage,
                    'max_coverage': max_cov,
                    'description': desc,
                    'is_active': True,
                },
            )
            self.insurance_plans.append(plan)

        self.counts['insurance_providers'] = len(providers_data)
        self.counts['insurance_plans'] = len(plans_data)
        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(providers_data)} providers, {len(plans_data)} plans'
        ))

    # ── 9. Doctors ───────────────────────────────────────────────────────

    def _create_doctors(self):
        self.stdout.write('Creating 10 doctors...')
        spec_names = list(self.specializations.keys())
        dept_list = list(self.departments.values())

        first_names_m = KENYAN_FIRST_NAMES_MALE[:6] + ENGLISH_FIRST_NAMES_MALE[:4]
        last_names = KENYAN_LAST_NAMES[:10]

        self.doctor_users = []
        self.doctor_objects = []
        for i in range(10):
            first = first_names_m[i]
            last = last_names[i]
            username = f'dr.{first.lower()}.{last.lower()}'
            email = f'{username}@medcare.co.ke'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'phone': ke.phone(),
                    'gender': 'Male',
                    'date_of_birth': date(random.randint(1965, 1990), random.randint(1, 12), random.randint(1, 28)),
                    'address': f'{random.randint(1, 200)}, {random.choice(["Kasarani", "Lavington", "Westlands", "Kilimani", "Karen", "South B"])}, Nairobi',
                },
            )
            if created:
                user.set_password('doctor123')
                user.save()
            self.doctor_users.append(user)

            role = Role.objects.get(name='Doctor')
            user.roles.add(role)

            dept = random.choice(dept_list)
            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept,
                    'designation': 'Senior Consultant',
                    'date_of_joining': date(random.randint(2015, 2023), random.randint(1, 12), 1),
                    'salary': random.choice([80000, 90000, 100000, 120000, 150000]),
                    'emergency_contact': f'{random.choice(KENYAN_FIRST_NAMES_MALE)} {last}',
                    'emergency_phone': ke.phone(),
                    'is_active': True,
                },
            )

            spec_name = spec_names[i % len(spec_names)]
            spec = self.specializations[spec_name]

            doc, _ = Doctor.objects.get_or_create(
                employee=emp,
                defaults={
                    'specialization': spec,
                    'consultation_fee': random.choice([500, 700, 800, 1000, 1200, 1500, 2000]),
                    'bio': f'Dr. {first} {last} is a experienced {spec_name} specialist with {random.randint(5, 25)} years of experience.',
                    'years_of_experience': random.randint(5, 25),
                    'is_available': True,
                },
            )
            self.doctor_objects.append(doc)

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            for day in days:
                DoctorSchedule.objects.get_or_create(
                    doctor=doc,
                    day_of_week=day,
                    start_time=time(9, 0),
                    defaults={'end_time': time(17, 0), 'is_active': True},
                )

        self.counts['doctors'] = 10
        self.stdout.write(self.style.SUCCESS('  Created 10 doctors with schedules'))

    # ── 10. Staff (Nurses, Receptionists, etc.) ──────────────────────────

    def _create_staff(self):
        self.stdout.write('Creating staff members...')
        dept_list = list(self.departments.values())

        staff_configs = [
            ('Nurse', 5, 'Nurse', [40000, 45000, 50000]),
            ('Receptionist', 2, 'Receptionist', [25000, 30000]),
            ('Pharmacist', 2, 'Pharmacist', [35000, 40000]),
            ('Lab Technician', 2, 'Lab Technician', [30000, 35000]),
            ('Accountant', 1, 'Accountant', [40000, 45000]),
            ('HR Manager', 1, 'HR Manager', [50000, 60000]),
        ]

        self.staff_users = []
        total_staff = 0
        for role_name, count, designation, salaries in staff_configs:
            role = Role.objects.get(name=role_name)
            for i in range(count):
                is_female = role_name in ['Nurse'] and random.random() > 0.3
                if is_female:
                    first = random.choice(KENYAN_FIRST_NAMES_FEMALE + ENGLISH_FIRST_NAMES_FEMALE)
                else:
                    first = random.choice(KENYAN_FIRST_NAMES_MALE + ENGLISH_FIRST_NAMES_MALE)
                last = random.choice(KENYAN_LAST_NAMES)

                uname = f'{first.lower()}.{last.lower()}.{role_name.lower().replace(" ", "")}{i+1}'
                email = f'{uname}@medcare.co.ke'

                user, created = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        'email': email,
                        'first_name': first,
                        'last_name': last,
                        'phone': ke.phone(),
                        'gender': 'Female' if is_female else 'Male',
                        'date_of_birth': date(random.randint(1985, 2000), random.randint(1, 12), random.randint(1, 28)),
                        'address': f'{random.randint(1, 200)}, {random.choice(["Kasarani", "Lavington", "Westlands", "Karen"])}, Nairobi',
                    },
                )
                if created:
                    user.set_password('staff123')
                    user.save()
                self.staff_users.append(user)

                user.roles.add(role)

                dept = random.choice(dept_list)
                Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'department': dept,
                        'designation': designation,
                        'date_of_joining': date(random.randint(2018, 2024), random.randint(1, 12), 1),
                        'salary': random.choice(salaries),
                        'emergency_contact': f'{random.choice(KENYAN_FIRST_NAMES_MALE)} {last}',
                        'emergency_phone': ke.phone(),
                        'is_active': True,
                    },
                )
                total_staff += 1

        self.counts['staff'] = total_staff
        self.stdout.write(self.style.SUCCESS(f'  Created {total_staff} staff members'))

    # ── 11. Patients ─────────────────────────────────────────────────────

    def _create_patients(self):
        self.stdout.write('Creating 50 patients...')
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

        self.patient_objects = []
        self.patient_users = []
        for i in range(50):
            is_female = random.random() > 0.45
            if is_female:
                first = random.choice(KENYAN_FIRST_NAMES_FEMALE + ENGLISH_FIRST_NAMES_FEMALE)
            else:
                first = random.choice(KENYAN_FIRST_NAMES_MALE + ENGLISH_FIRST_NAMES_MALE)
            last = random.choice(KENYAN_LAST_NAMES)

            uname = f'{first.lower()}.{last.lower()}.p{i+1}'
            email = f'{uname}@email.com'

            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'phone': ke.phone(),
                    'gender': 'Female' if is_female else 'Male',
                    'date_of_birth': date(random.randint(1950, 2015), random.randint(1, 12), random.randint(1, 28)),
                    'address': f'{random.randint(1, 500)}, {random.choice(["Kasarani", "Lavington", "Westlands", "Kilimani", "Karen", "South B", "Industrial Area", "Ngara", "Parklands", "CBD"])}, Nairobi',
                },
            )
            if created:
                user.set_password('patient123')
                user.save()
            self.patient_users.append(user)

            role = Role.objects.get(name='Patient')
            user.roles.add(role)

            plan = random.choice(self.insurance_plans) if random.random() > 0.4 else None

            patient, _ = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'blood_group': random.choice(blood_groups),
                    'allergies': random.choice(ALLERGIES),
                    'medical_history': random.choice(MEDICAL_HISTORIES),
                    'emergency_contact_name': f'{random.choice(KENYAN_FIRST_NAMES_MALE)} {last}',
                    'emergency_contact_phone': ke.phone(),
                    'insurance_provider': plan,
                },
            )
            self.patient_objects.append(patient)

        self.counts['patients'] = 50
        self.stdout.write(self.style.SUCCESS('  Created 50 patients'))

    # ── 12. Appointments ─────────────────────────────────────────────────

    def _create_appointments(self):
        self.stdout.write('Creating 100 appointments...')
        today = timezone.now().date()
        statuses = ['Scheduled', 'Confirmed', 'In-Progress', 'Completed', 'Cancelled', 'No-Show']
        status_weights = [10, 15, 5, 50, 10, 10]
        types = ['OPD', 'IPD', 'EMERGENCY', 'ONLINE']
        type_weights = [60, 15, 15, 10]

        self.appointment_objects = []
        for i in range(100):
            patient = random.choice(self.patient_objects)
            doctor = random.choice(self.doctor_objects)
            days_ago = random.randint(0, 30)
            appt_date = today - timedelta(days=days_ago)
            appt_time = random.choice(TIME_SLOTS)
            status = random.choices(statuses, weights=status_weights, k=1)[0]
            appt_type = random.choices(types, weights=type_weights, k=1)[0]

            dept = doctor.employee.department

            appt, _ = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                appointment_date=appt_date,
                appointment_time=appt_time,
                defaults={
                    'department': dept,
                    'appointment_type': appt_type,
                    'status': status,
                    'reason': random.choice(APPOINTMENT_REASONS),
                    'notes': random.choice(DOCTOR_NOTES) if status in ['Completed', 'In-Progress'] else '',
                },
            )
            self.appointment_objects.append(appt)

            if status == 'Completed':
                Visit.objects.get_or_create(
                    appointment=appt,
                    defaults={
                        'doctor_notes': random.choice(DOCTOR_NOTES),
                        'diagnosis': random.choice(DIAGNOSES),
                        'follow_up_date': appt_date + timedelta(days=random.randint(7, 30)) if random.random() > 0.5 else None,
                    },
                )

        self.counts['appointments'] = 100
        completed = sum(1 for a in self.appointment_objects if a.status == 'Completed')
        self.counts['visits'] = completed
        self.stdout.write(self.style.SUCCESS(f'  Created 100 appointments ({completed} with visits)'))

    # ── 13. Prescriptions ────────────────────────────────────────────────

    def _create_prescriptions(self):
        self.stdout.write('Creating 50 prescriptions...')
        completed_visits = list(Visit.objects.select_related('appointment__patient', 'appointment__doctor'))

        if not completed_visits:
            self.stdout.write(self.style.WARNING('  No completed visits found, skipping prescriptions'))
            self.counts['prescriptions'] = 0
            self.counts['prescription_items'] = 0
            return

        random.shuffle(completed_visits)
        visits_to_use = completed_visits[:50]

        prescription_items_count = 0
        for visit in visits_to_use:
            appt = visit.appointment
            patient = appt.patient
            doctor_user = appt.doctor.employee.user

            prescription, _ = Prescription.objects.get_or_create(
                visit=visit,
                defaults={
                    'doctor': doctor_user,
                    'patient': patient,
                    'diagnosis': visit.diagnosis or random.choice(DIAGNOSES),
                    'notes': visit.doctor_notes or '',
                    'is_dispensed': random.random() > 0.3,
                },
            )

            num_items = random.randint(1, 4)
            for _ in range(num_items):
                med = random.choice(self.medicines)
                PrescriptionItem.objects.get_or_create(
                    prescription=prescription,
                    medicine=med,
                    defaults={
                        'dosage': random.choice(DOSAGES),
                        'frequency': random.choice(FREQUENCIES),
                        'duration': random.choice(DURATIONS),
                        'quantity': random.randint(1, 30),
                        'instructions': random.choice([
                            'Take after meals', 'Take before meals',
                            'Take with water', 'Take at bedtime',
                            'As needed for pain', 'Complete the full course',
                        ]),
                    },
                )
                prescription_items_count += 1

        self.counts['prescriptions'] = len(visits_to_use)
        self.counts['prescription_items'] = prescription_items_count
        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(visits_to_use)} prescriptions with {prescription_items_count} items'
        ))

    # ── 14. Lab Orders ───────────────────────────────────────────────────

    def _create_lab_orders(self):
        self.stdout.write('Creating 50 lab orders with results...')
        lab_tests_data = [
            ('Complete Blood Count (CBC)', 'Measures blood cell components', 350, '4.0-11.0', 'x10^3/uL'),
            ('Blood Sugar (Fasting)', 'Measures fasting blood glucose level', 150, '70-100', 'mg/dL'),
            ('Blood Sugar (Random)', 'Measures random blood glucose level', 150, '70-140', 'mg/dL'),
            ('Lipid Profile', 'Measures cholesterol and triglycerides', 500, '<200', 'mg/dL'),
            ('Liver Function Test (LFT)', 'Measures liver enzymes and function', 600, 'Normal range varies', 'U/L'),
            ('Kidney Function Test (KFT)', 'Measures kidney function markers', 550, '0.6-1.2', 'mg/dL'),
            ('Thyroid Profile (TSH)', 'Measures thyroid stimulating hormone', 450, '0.4-4.0', 'mIU/L'),
            ('Hemoglobin (Hb)', 'Measures hemoglobin level', 120, '12-16', 'g/dL'),
            ('Urinalysis', 'Analysis of urine sample', 200, 'Normal', ''),
            ('ECG', 'Electrocardiogram test', 400, 'Normal sinus rhythm', ''),
            ('Chest X-Ray', 'X-ray of chest region', 600, 'No abnormality', ''),
            ('Blood Group & RH', 'Determines blood group', 180, 'N/A', ''),
            ('HbA1c', 'Glycated hemoglobin test', 400, '<5.7', '%'),
            ('ESR', 'Erythrocyte sedimentation rate', 150, '0-20', 'mm/hr'),
            ('CRP', 'C-Reactive Protein', 300, '<3.0', 'mg/L'),
        ]

        dept_pathology = self.departments.get('Pathology')
        dept_radiology = self.departments.get('Radiology')

        lab_tests = []
        for name, desc, price, normal_range, unit in lab_tests_data:
            dept = dept_radiology if 'X-Ray' in name or 'ECG' in name else dept_pathology
            test, _ = LabTest.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'department': dept,
                    'price': price,
                    'normal_range': normal_range,
                    'unit': unit,
                    'is_active': True,
                },
            )
            lab_tests.append(test)

        lab_tech_user = User.objects.filter(roles__name='Lab Technician').first()
        if not lab_tech_user:
            lab_tech_user = self.doctor_users[0]

        today = timezone.now().date()
        lab_order_items_count = 0
        lab_results_count = 0

        for i in range(50):
            patient = random.choice(self.patient_objects)
            doctor = random.choice(self.doctor_objects)
            days_ago = random.randint(0, 30)
            order_date = today - timedelta(days=days_ago)

            status = random.choices(
                ['Pending', 'In-Progress', 'Completed', 'Cancelled'],
                weights=[20, 10, 65, 5], k=1
            )[0]
            priority = random.choices(['Routine', 'Urgent', 'STAT'], weights=[70, 25, 5], k=1)[0]

            order, _ = LabOrder.objects.get_or_create(
                patient=patient,
                doctor=doctor.employee.user,
                defaults={
                    'status': status,
                    'priority': priority,
                    'created_at': timezone.make_aware(
                        timezone.datetime.combine(order_date, time(9, 0))
                    ),
                    'completed_at': timezone.make_aware(
                        timezone.datetime.combine(order_date + timedelta(days=random.randint(1, 3)), time(14, 0))
                    ) if status == 'Completed' else None,
                },
            )

            num_tests = random.randint(1, 3)
            selected_tests = random.sample(lab_tests, min(num_tests, len(lab_tests)))
            for test in selected_tests:
                order_item, _ = LabOrderItem.objects.get_or_create(
                    order=order,
                    test=test,
                    defaults={'notes': ''},
                )
                lab_order_items_count += 1

                if status == 'Completed':
                    is_abnormal = random.random() > 0.7
                    LabResult.objects.get_or_create(
                        order_item=order_item,
                        defaults={
                            'result_value': f'{random.uniform(3.5, 15.0):.1f}',
                            'reference_range': test.normal_range,
                            'is_abnormal': is_abnormal,
                            'notes': 'Abnormal - requires follow-up' if is_abnormal else 'Within normal range',
                            'uploaded_by': lab_tech_user,
                        },
                    )
                    lab_results_count += 1

        self.counts['lab_orders'] = 50
        self.counts['lab_order_items'] = lab_order_items_count
        self.counts['lab_results'] = lab_results_count
        self.stdout.write(self.style.SUCCESS(
            f'  Created 50 lab orders, {lab_order_items_count} items, {lab_results_count} results'
        ))

    # ── 15. Invoices ─────────────────────────────────────────────────────

    def _create_invoices(self):
        self.stdout.write('Creating 50 invoices with payments...')
        accountant = User.objects.filter(roles__name='Accountant').first()
        if not accountant:
            accountant = self.staff_users[0] if self.staff_users else self.doctor_users[0]

        today = timezone.now().date()
        payment_methods = ke.PAYMENT_METHODS

        self.invoice_objects = []
        total_payments = 0

        for i in range(50):
            patient = random.choice(self.patient_objects)
            appt = random.choice(self.appointment_objects) if self.appointment_objects else None
            days_ago = random.randint(0, 30)
            inv_date = today - timedelta(days=days_ago)

            total_amount = Decimal(str(random.randint(500, 15000)))
            discount = Decimal(str(random.randint(0, int(total_amount * Decimal('0.15')))))
            tax = Decimal(str(int((total_amount - discount) * Decimal('0.05'))))
            net_amount = total_amount - discount + tax

            status = random.choices(
                ['Pending', 'Partial', 'Paid', 'Cancelled'],
                weights=[20, 20, 55, 5], k=1
            )[0]

            paid_amount = Decimal('0')
            if status == 'Paid':
                paid_amount = net_amount
            elif status == 'Partial':
                paid_amount = Decimal(str(int(net_amount * Decimal(str(random.uniform(0.3, 0.8))))))

            invoice, _ = Invoice.objects.get_or_create(
                patient=patient,
                appointment=appt,
                defaults={
                    'total_amount': total_amount,
                    'discount': discount,
                    'tax': tax,
                    'net_amount': net_amount,
                    'status': status,
                    'paid_amount': paid_amount,
                    'due_amount': net_amount - paid_amount,
                    'notes': random.choice(['', 'Insurance claim pending', 'Discount applied for senior citizen', '']),
                    'created_by': accountant,
                },
            )
            self.invoice_objects.append(invoice)

            descriptions = [
                ('Consultation Fee', 1, 500),
                ('Registration Fee', 1, 100),
                ('Pathology - CBC', 1, 350),
                ('Pathology - Blood Sugar', 1, 150),
                ('Radiology - Chest X-Ray', 1, 600),
                ('Medicine Charges', random.randint(1, 5), random.randint(50, 500)),
                ('Bed Charge (per day)', random.randint(1, 3), 2000),
                ('Procedure Charge', 1, random.randint(1000, 5000)),
            ]

            num_items = random.randint(2, 5)
            selected_items = random.sample(descriptions, min(num_items, len(descriptions)))
            for desc, qty, unit_price in selected_items:
                InvoiceItem.objects.get_or_create(
                    invoice=invoice,
                    description=desc,
                    defaults={
                        'quantity': qty,
                        'unit_price': unit_price,
                        'total_price': qty * unit_price,
                    },
                )

            if paid_amount > 0:
                Payment.objects.get_or_create(
                    invoice=invoice,
                    amount=paid_amount,
                    defaults={
                        **ke.payment(payment_methods),
                        'received_by': accountant,
                        'notes': '',
                    },
                )
                total_payments += 1

        self.counts['invoices'] = 50
        self.counts['invoice_items'] = InvoiceItem.objects.count()
        self.counts['payments'] = total_payments
        self.stdout.write(self.style.SUCCESS(
            f'  Created 50 invoices, {InvoiceItem.objects.count()} items, {total_payments} payments'
        ))

    # ── Summary ──────────────────────────────────────────────────────────

    def _print_summary(self):
        self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 60))
        self.stdout.write(self.style.HTTP_INFO('         DEMO DATA SEEDING COMPLETE'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))

        summary_items = [
            ('Roles', self.counts.get('roles', 0)),
            ('Super Admin', self.counts.get('super_admin', 0)),
            ('Hospital Admin', self.counts.get('hospital_admin', 0)),
            ('Branches', self.counts.get('branches', 0)),
            ('Departments', self.counts.get('departments', 0)),
            ('Specializations', self.counts.get('specializations', 0)),
            ('Doctors', self.counts.get('doctors', 0)),
            ('Staff Members', self.counts.get('staff', 0)),
            ('Patients', self.counts.get('patients', 0)),
            ('Appointments', self.counts.get('appointments', 0)),
            ('Visits', self.counts.get('visits', 0)),
            ('Prescriptions', self.counts.get('prescriptions', 0)),
            ('Prescription Items', self.counts.get('prescription_items', 0)),
            ('Lab Orders', self.counts.get('lab_orders', 0)),
            ('Lab Order Items', self.counts.get('lab_order_items', 0)),
            ('Lab Results', self.counts.get('lab_results', 0)),
            ('Invoices', self.counts.get('invoices', 0)),
            ('Invoice Items', self.counts.get('invoice_items', 0)),
            ('Payments', self.counts.get('payments', 0)),
            ('Medicine Categories', self.counts.get('medicine_categories', 0)),
            ('Suppliers', self.counts.get('suppliers', 0)),
            ('Medicines', self.counts.get('medicines', 0)),
            ('Insurance Providers', self.counts.get('insurance_providers', 0)),
            ('Insurance Plans', self.counts.get('insurance_plans', 0)),
        ]

        for label, count in summary_items:
            self.stdout.write(f'  {label:<25} : {count}')

        total = sum(count for _, count in summary_items)
        self.stdout.write(self.style.HTTP_INFO('-' * 60))
        self.stdout.write(self.style.SUCCESS(f'  {"TOTAL RECORDS":<25} : {total}'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))

        self.stdout.write(self.style.HTTP_INFO('\n  Login Credentials:'))
        self.stdout.write('  Super Admin   : admin / admin123')
        self.stdout.write('  Hospital Admin: hospitaladmin / admin123')
        self.stdout.write('  Doctors       : dr.<first>.<last> / doctor123')
        self.stdout.write('  Staff         : <first>.<last>.<role> / staff123')
        self.stdout.write('  Patients      : <first>.<last>.p<id> / patient123')
        self.stdout.write(self.style.HTTP_INFO(''))
