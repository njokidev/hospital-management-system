import random
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from django.core.management.base import BaseCommand

from core import seed_kenya as ke
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive demo data for MEDCARE Hospital Management System'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write('Clearing all existing data...')
        from django.core.management import call_command
        from django.apps import apps
        for model in apps.get_models():
            try:
                model.objects.all().delete()
            except Exception:
                pass
        self.stdout.write('  All data cleared.')

        self.stdout.write('Creating comprehensive demo data...')
        self.today = timezone.now().date()
        self.now = timezone.now()

        with transaction.atomic():
            self._create_roles()
            self._create_admin()
            self._create_branch()
            self._create_departments()
            self._create_specializations()
            self._create_insurance()
            self._create_doctors()
            self._create_nurses()
            self._create_pharmacists()
            self._create_lab_techs()
            self._create_accountants()
            self._create_receptionists()
            self._create_patients()
            self._create_appointments()
            self._create_opd_visits()
            self._create_prescriptions()
            self._create_lab_data()
            self._create_radiology_data()
            self._create_billing()
            self._create_ipd()
            self._create_nursing()
            self._create_ambulance()
            self._create_inventory()
            self._create_hr()
            self._create_notifications()
            self._create_audit_logs()

        self._print_summary()

    def _ke_staff_ids(self, role=None):
        """Kenyan statutory and professional identifiers for a staff member."""
        ids = {
            'national_id': ke.national_id(),
            'kra_pin': ke.kra_pin(),
            'nssf_number': ke.nssf_number(),
            'sha_number': ke.sha_number(),
        }
        body = ke.REGULATOR_BY_ROLE.get(role)
        if body:
            ids.update({
                'regulatory_body': body,
                'license_number': ke.licence_number(body),
                'license_expiry': date(self.today.year, 12, 31) if hasattr(self, 'today') else date(date.today().year, 12, 31),
            })
        return ids

    def _create_roles(self):
        from accounts.models import Role
        role_names = [
            'Super Admin', 'Hospital Admin', 'Doctor', 'Nurse',
            'Receptionist', 'Pharmacist', 'Lab Technician',
            'Accountant', 'HR Manager', 'Patient'
        ]
        self.roles = {}
        for name in role_names:
            role, _ = Role.objects.get_or_create(name=name, defaults={'description': f'{name} role'})
            self.roles[name] = role
        self.stdout.write('  Roles created.')

    def _create_admin(self):
        self.admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@medcare.co.ke',
                'first_name': 'System',
                'last_name': 'Administrator',
                'phone': '+254700000000',
                'gender': 'Male',
                'date_of_birth': date(1985, 1, 15),
                'address': ke.HOSPITAL_ADDRESS,
                'is_superuser': True,
                'is_staff': True,
            }
        )
        self.admin_user.set_password('admin123')
        self.admin_user.save()
        self.admin_user.roles.add(self.roles['Super Admin'])
        self.stdout.write('  Admin user created.')

    def _create_branch(self):
        from hospitals.models import Branch
        self.branch = Branch.objects.create(
            name='MEDCARE Upper Hill (Main)',
            address=ke.HOSPITAL_ADDRESS,
            county='Nairobi', mfl_code='99999', keph_level=5, sha_accredited=True,
            phone='+254700000001', is_main_branch=True
        )
        self.stdout.write('  Branch created.')

    def _create_departments(self):
        from departments.models import Department
        dept_data = [
            ('Cardiology', 'Heart and cardiovascular system'),
            ('Neurology', 'Brain and nervous system'),
            ('Pediatrics', 'Children healthcare'),
            ('Orthopedics', 'Bones and joints'),
            ('Dermatology', 'Skin conditions'),
            ('ENT', 'Ear, Nose, and Throat'),
            ('Oncology', 'Cancer treatment'),
            ('Gynecology', 'Women healthcare'),
            ('Radiology', 'Medical imaging'),
            ('Pathology', 'Disease diagnosis'),
            ('Emergency Medicine', 'Emergency care'),
            ('General Medicine', 'General healthcare'),
            ('Surgery', 'Surgical procedures'),
            ('Pharmacy', 'Medications'),
        ]
        self.departments = {}
        for name, desc in dept_data:
            dept = Department.objects.create(
                name=name, description=desc, branch=self.branch,
                phone=ke.landline(),
                email=f'{name.lower().replace(" ", "")}@medcare.co.ke'
            )
            self.departments[name] = dept
        self.stdout.write('  Departments created.')

    def _create_specializations(self):
        from departments.models import Specialization
        spec_data = {
            'Cardiology': ['Interventional Cardiology', 'Electrophysiology', 'Heart Failure'],
            'Neurology': ['Stroke', 'Epilepsy', 'Movement Disorders'],
            'Pediatrics': ['Neonatology', 'Pediatric Surgery', 'Pediatric Cardiology'],
            'Orthopedics': ['Spine Surgery', 'Joint Replacement', 'Sports Medicine'],
            'Dermatology': ['Cosmetic Dermatology', 'Dermatopathology'],
            'ENT': ['Otology', 'Rhinology', 'Laryngology'],
            'Oncology': ['Medical Oncology', 'Radiation Oncology', 'Surgical Oncology'],
            'Gynecology': ['Obstetrics', 'Reproductive Endocrinology', 'Gynecologic Oncology'],
            'Radiology': ['Diagnostic Radiology', 'Interventional Radiology'],
            'Pathology': ['Clinical Pathology', 'Anatomical Pathology'],
            'Emergency Medicine': ['Trauma', 'Critical Care'],
            'General Medicine': ['Internal Medicine', 'Family Medicine'],
            'Surgery': ['General Surgery', 'Cardiac Surgery', 'Neurosurgery'],
            'Pharmacy': ['Clinical Pharmacy', 'Hospital Pharmacy'],
        }
        self.specializations = {}
        for dept_name, specs in spec_data.items():
            for spec_name in specs:
                spec = Specialization.objects.create(
                    name=spec_name, department=self.departments[dept_name]
                )
                self.specializations[spec_name] = spec
        self.stdout.write('  Specializations created.')

    def _create_insurance(self):
        from insurance.models import InsuranceProvider, InsurancePlan
        providers = [(name, 'Provider Relations', ke.phone()) for name in ke.INSURERS]
        self.plans = []
        for name, contact, phone in providers:
            provider = InsuranceProvider.objects.create(
                name=name, contact_person=contact, phone=phone,
                email=f'claims@{name.split()[0].lower().strip("()")}.example.com'
            )
            if 'SHA' in name:
                plan_data = [
                    ('SHIF – Primary Healthcare', 100, 0),
                    ('SHIF – Social Health Insurance Fund', 100, 0),
                ]
            else:
                plan_data = [
                    ('Bronze (Outpatient KSh 50k / Inpatient KSh 500k)', 80, 500000),
                    ('Silver (Outpatient KSh 100k / Inpatient KSh 1M)', 90, 1000000),
                    ('Gold (Outpatient KSh 200k / Inpatient KSh 3M)', 100, 3000000),
                ]
            for plan_name, coverage, max_cov in plan_data:
                plan = InsurancePlan.objects.create(
                    provider=provider, name=f'{name} {plan_name}',
                    coverage_percentage=coverage, max_coverage=Decimal(str(max_cov)),
                    description=f'{plan_name} with {coverage}% coverage'
                )
                self.plans.append(plan)
        self.stdout.write('  Insurance created.')

    def _create_doctors(self):
        from employees.models import Employee
        from doctors.models import Doctor, DoctorSchedule
        doctor_data = [
            ('Wanjiku', 'Kamau', 'Female', 'Cardiology', 'Interventional Cardiology', 5000, 15),
            ('Brian', 'Otieno', 'Male', 'Neurology', 'Stroke', 4500, 12),
            ('Achieng', 'Odhiambo', 'Female', 'Pediatrics', 'Neonatology', 3500, 10),
            ('Kiprop', 'Koech', 'Male', 'Gynecology', 'Obstetrics', 4000, 8),
            ('Mutua', 'Musyoka', 'Male', 'Orthopedics', 'Joint Replacement', 4500, 20),
            ('Fatuma', 'Hassan', 'Female', 'Dermatology', 'Cosmetic Dermatology', 3000, 6),
            ('Peter', 'Wekesa', 'Male', 'ENT', 'Rhinology', 3000, 11),
            ('Njeri', 'Mwangi', 'Female', 'Oncology', 'Medical Oncology', 5000, 14),
            ('Samuel', 'Kariuki', 'Male', 'Surgery', 'General Surgery', 5000, 18),
            ('Chebet', 'Rotich', 'Female', 'General Medicine', 'Internal Medicine', 2500, 9),
            ('Abdi', 'Mohamed', 'Male', 'Radiology', 'Diagnostic Radiology', 3500, 7),
            ('Nafula', 'Barasa', 'Female', 'Pathology', 'Clinical Pathology', 3000, 5),
        ]
        self.doctors = []
        for first, last, gender, dept, spec, fee, exp in doctor_data:
            username = f'dr.{first.lower()}.{last.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}.{last.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': gender,
                    'date_of_birth': date(self.today.year - exp - random.randint(25, 35), random.randint(1, 12), random.randint(1, 28)),
                    'address': ke.address(),
                }
            )
            user.set_password('doctor123')
            user.save()
            user.roles.add(self.roles['Doctor'])
            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': self.departments[dept],
                    'designation': 'Senior Consultant',
                    'date_of_joining': date.today() - timedelta(days=365 * exp),
                    'salary': Decimal(str(random.randint(25, 60) * 10000)),
                    **self._ke_staff_ids('Doctor'),
                }
            )
            doc, _ = Doctor.objects.get_or_create(
                employee=emp,
                defaults={
                    'specialization': self.specializations.get(spec),
                    'consultation_fee': Decimal(str(fee)),
                    'years_of_experience': exp,
                    'bio': f'{first} {last} - {spec} specialist with {exp} years of experience.',
                }
            )
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            for day in days[:random.randint(3, 5)]:
                DoctorSchedule.objects.get_or_create(
                    doctor=doc, day_of_week=day, start_time=time(9, 0),
                    defaults={'end_time': time(17, 0)},
                )
            self.doctors.append((user, doc))
        self.stdout.write('  Doctors created.')

    def _create_nurses(self):
        from employees.models import Employee
        nurse_data = [
            ('Grace', 'Wambui'), ('Mercy', 'Akinyi'), ('Faith', 'Chebet'),
            ('Esther', 'Mumbua'), ('Purity', 'Nyambura'),
        ]
        self.nurses = []
        for first, last in nurse_data:
            username = f'nurse.{first.lower()}.{last.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}.{last.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': 'Female',
                    'date_of_birth': date(random.randint(1985, 1995), random.randint(1, 12), random.randint(1, 28)),
                }
            )
            user.set_password('nurse123')
            user.save()
            user.roles.add(self.roles['Nurse'])
            dept = random.choice([self.departments['General Medicine'], self.departments['Cardiology'], self.departments['Surgery']])
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept, 'designation': 'Registered Nurse (KRCHN)',
                    'date_of_joining': date.today() - timedelta(days=random.randint(365, 1825)),
                    'salary': Decimal(str(random.randint(7, 12) * 10000)),
                    **self._ke_staff_ids('Nurse'),
                }
            )
            self.nurses.append(user)
        self.stdout.write('  Nurses created.')

    def _create_pharmacists(self):
        from employees.models import Employee
        self.pharmacists = []
        for first, last in [('Collins', 'Njoroge'), ('Lilian', 'Atieno')]:
            username = f'pharmacist.{first.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': random.choice(['Male', 'Female']),
                }
            )
            user.set_password('pharmacist123')
            user.save()
            user.roles.add(self.roles['Pharmacist'])
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': self.departments['Pharmacy'],
                    'designation': 'Senior Pharmacist',
                    'date_of_joining': date.today() - timedelta(days=random.randint(365, 1825)),
                    'salary': Decimal(str(random.randint(9, 15) * 10000)),
                    **self._ke_staff_ids('Pharmacist'),
                }
            )
            self.pharmacists.append(user)
        self.stdout.write('  Pharmacists created.')

    def _create_lab_techs(self):
        from employees.models import Employee
        self.lab_techs = []
        for first, last in [('Dennis', 'Ochieng'), ('Caroline', 'Wanjala')]:
            username = f'labtech.{first.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': random.choice(['Male', 'Female']),
                }
            )
            user.set_password('lab123')
            user.save()
            user.roles.add(self.roles['Lab Technician'])
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': self.departments['Pathology'],
                    'designation': 'Medical Laboratory Technologist',
                    'date_of_joining': date.today() - timedelta(days=random.randint(365, 1825)),
                    'salary': Decimal(str(random.randint(5, 9) * 10000)),
                    **self._ke_staff_ids('Lab Technician'),
                }
            )
            self.lab_techs.append(user)
        self.stdout.write('  Lab Technicians created.')

    def _create_accountants(self):
        from employees.models import Employee
        self.accountants = []
        for first, last in [('Kevin', 'Kimani'), ('Joy', 'Muriuki')]:
            username = f'accountant.{first.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': random.choice(['Male', 'Female']),
                }
            )
            user.set_password('accountant123')
            user.save()
            user.roles.add(self.roles['Accountant'])
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': self.departments['General Medicine'],
                    'designation': 'Senior Accountant',
                    'date_of_joining': date.today() - timedelta(days=random.randint(365, 1825)),
                    'salary': Decimal(str(random.randint(7, 13) * 10000)),
                    **self._ke_staff_ids(),
                }
            )
            self.accountants.append(user)
        self.stdout.write('  Accountants created.')

    def _create_receptionists(self):
        from employees.models import Employee
        self.receptionists = []
        for first, last in [('Victor', 'Gitau'), ('Amina', 'Ali')]:
            username = f'receptionist.{first.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}@medcare.co.ke',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': random.choice(['Male', 'Female']),
                }
            )
            user.set_password('receptionist123')
            user.save()
            user.roles.add(self.roles['Receptionist'])
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': self.departments['General Medicine'],
                    'designation': 'Front Desk',
                    'date_of_joining': date.today() - timedelta(days=random.randint(365, 1825)),
                    'salary': Decimal(str(random.randint(3, 5) * 10000)),
                    **self._ke_staff_ids(),
                }
            )
            self.receptionists.append(user)
        self.stdout.write('  Receptionists created.')

    def _create_patients(self):
        from patients.models import Patient
        from insurance.models import PatientInsurance
        patient_data = [
            ('Zawadi', 'Njoroge', 'Female', 'A+'),
            ('Juma', 'Omondi', 'Male', 'B+'),
            ('Neema', 'Mutua', 'Female', 'AB+'),
            ('Felix', 'Kiprotich', 'Male', 'A-'),
            ('Wambui', 'Gitau', 'Female', 'O+'),
            ('Hassan', 'Abdi', 'Male', 'B-'),
            ('Akinyi', 'Ochieng', 'Female', 'O+'),
            ('Daniel', 'Ndungu', 'Male', 'A+'),
            ('Jepkosgei', 'Cheruiyot', 'Female', 'B-'),
            ('Joseph', 'Wafula', 'Male', 'O+'),
            ('Muthoni', 'Kariuki', 'Female', 'AB+'),
            ('Mohamed', 'Ali', 'Male', 'B+'),
            ('Naliaka', 'Wekesa', 'Female', 'A+'),
            ('James', 'Onyango', 'Male', 'O+'),
            ('Mumbua', 'Musyoka', 'Female', 'AB+'),
            ('John', 'Kamau', 'Male', 'O+'),
            ('Atieno', 'Odhiambo', 'Female', 'A-'),
            ('Kibet', 'Koech', 'Male', 'B+'),
            ('Njeri', 'Kimani', 'Female', 'O-'),
            ('Otieno', 'Barasa', 'Male', 'A+'),
            ('Fatuma', 'Mohamed', 'Female', 'B-'),
            ('Mwangi', 'Muriuki', 'Male', 'AB-'),
            ('Chebet', 'Rotich', 'Female', 'O+'),
            ('Kamau', 'Nyambura', 'Male', 'A+'),
            ('Faith', 'Wanjala', 'Female', 'B+'),
        ]
        self.patients = []
        for i, (first, last, gender, blood) in enumerate(patient_data):
            username = f'patient.{first.lower()}.{last.lower()}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{first.lower()}.{last.lower()}@email.com',
                    'first_name': first, 'last_name': last,
                    'phone': ke.phone(),
                    'gender': gender,
                    'date_of_birth': date(2026 - random.randint(20, 65), random.randint(1, 12), random.randint(1, 28)),
                    'address': ke.address(),
                }
            )
            user.set_password('patient123')
            user.save()
            user.roles.add(self.roles['Patient'])
            county, sub_county, ward = ke.residence()
            pat, _ = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'id_type': 'national_id',
                    'id_number': ke.national_id(),
                    'sha_number': ke.sha_number() if random.random() > 0.15 else '',
                    'county': county, 'sub_county': sub_county, 'ward': ward,
                    'emergency_contact_relationship': random.choice(['Spouse', 'Parent', 'Sibling', 'Child']),
                    'blood_group': blood,
                    'allergies': random.choice(['None', 'Penicillin', 'Sulfa drugs', 'Dust', 'Pollen']),
                    'medical_history': random.choice(['None', 'Diabetes', 'Hypertension', 'Asthma', 'Malaria (treated)', 'Sickle cell trait']),
                    'emergency_contact_name': f'{last} Family',
                    'emergency_contact_phone': ke.phone(),
                }
            )
            if random.random() > 0.3 and self.plans:
                plan = random.choice(self.plans)
                policy_num = f'POL-{self.today.year}-{str(i+1).zfill(4)}'
                PatientInsurance.objects.get_or_create(
                    policy_number=policy_num,
                    defaults={
                        'patient': pat, 'plan': plan,
                        'start_date': self.today - timedelta(days=random.randint(30, 180)),
                        'end_date': self.today + timedelta(days=random.randint(180, 365)),
                    }
                )
            self.patients.append((user, pat))
        self.stdout.write('  Patients created.')

    def _create_appointments(self):
        from appointments.models import Appointment, Visit
        statuses = ['Scheduled', 'Confirmed', 'In-Progress', 'Completed', 'Cancelled', 'No-Show']
        status_weights = [0.15, 0.15, 0.1, 0.4, 0.15, 0.05]
        reasons = [
            'General checkup', 'Follow-up visit', 'Chest pain',
            'Headache consultation', 'Routine blood work review',
            'Post-surgery follow-up', 'Chronic pain management',
            'Fever and cold', 'Back pain', 'Skin rash',
        ]
        self.appointments = []

        # Create appointments spread across the last 60 days + today + future
        for day_offset in range(-60, 8):
            appt_date = self.today + timedelta(days=day_offset)
            num_appts = random.randint(2, 6) if day_offset != 0 else random.randint(4, 8)
            for _ in range(num_appts):
                user_p, pat = random.choice(self.patients)
                doc_user, doc = random.choice(self.doctors)
                if day_offset == 0:
                    status = random.choice(['Scheduled', 'Confirmed', 'In-Progress', 'Completed'])
                elif day_offset < 0:
                    status = random.choices(statuses, weights=status_weights)[0]
                else:
                    status = 'Scheduled'

                appt = Appointment.objects.create(
                    patient=pat, doctor=doc,
                    appointment_date=appt_date,
                    appointment_time=time(random.randint(9, 16), random.choice([0, 30])),
                    department=doc.employee.department,
                    appointment_type=random.choice(['OPD', 'OPD', 'OPD', 'EMERGENCY', 'ONLINE']),
                    status=status,
                    reason=random.choice(reasons),
                )
                self.appointments.append(appt)

                # Create Visit for completed appointments
                if status == 'Completed':
                    Visit.objects.create(
                        appointment=appt,
                        doctor_notes='Patient responded well to treatment.',
                        diagnosis=random.choice([
                            'Viral infection', 'Hypertension', 'Type 2 Diabetes',
                            'Migraine', 'Gastritis', 'Lower back pain',
                            'Upper respiratory infection', 'Allergic reaction',
                        ]),
                        follow_up_date=appt_date + timedelta(days=random.randint(7, 30)),
                    )
        self.stdout.write('  Appointments created.')

    def _create_opd_visits(self):
        from opd.models import OPDVisit

        completed_diagnoses = [
            'Viral fever', 'Hypertension follow-up', 'Gastritis',
            'Migraine', 'Lower back strain', 'Allergic rhinitis',
        ]
        symptoms = [
            'Fever and body ache', 'Headache and nausea', 'Chest discomfort',
            'Abdominal pain', 'Cough and sore throat', 'Back pain',
        ]
        self.opd_visits = []
        opd_appointments = [a for a in self.appointments if a.appointment_type == 'OPD']

        for appt in opd_appointments[:120]:
            visit, _ = OPDVisit.objects.get_or_create(
                appointment=appt,
                defaults={
                    'patient': appt.patient,
                    'doctor': appt.doctor,
                    'visit_date': appt.appointment_date,
                    'symptoms': random.choice(symptoms),
                    'diagnosis': random.choice(completed_diagnoses) if appt.status == 'Completed' else '',
                    'treatment': 'Medication and follow-up advised' if appt.status == 'Completed' else '',
                    'doctor_notes': appt.notes or 'OPD consultation recorded.',
                    'follow_up_date': appt.appointment_date + timedelta(days=random.randint(7, 21)) if appt.status == 'Completed' else None,
                    'status': 'Completed' if appt.status == 'Completed' else random.choice(['Waiting', 'In-Progress', 'Referred']),
                },
            )
            self.opd_visits.append(visit)

        today_appts = [a for a in self.appointments if a.appointment_date == self.today and a.appointment_type == 'OPD']
        for appt in today_appts:
            visit, _ = OPDVisit.objects.get_or_create(
                appointment=appt,
                defaults={
                    'patient': appt.patient,
                    'doctor': appt.doctor,
                    'visit_date': self.today,
                    'symptoms': random.choice(symptoms),
                    'status': random.choice(['Waiting', 'In-Progress', 'Completed']),
                },
            )
            self.opd_visits.append(visit)

        if not OPDVisit.objects.filter(visit_date=self.today).exists():
            for appt in self.appointments[:5]:
                visit = OPDVisit.objects.create(
                    patient=appt.patient,
                    doctor=appt.doctor,
                    appointment=appt,
                    visit_date=self.today,
                    symptoms=random.choice(symptoms),
                    status=random.choice(['Waiting', 'In-Progress', 'Completed']),
                )
                self.opd_visits.append(visit)
        self.stdout.write('  OPD visits created.')

    def _create_prescriptions(self):
        from pharmacy.models import Medicine, MedicineCategory, Supplier, Prescription, PrescriptionItem, DispensedMedicine
        from appointments.models import Visit

        category_map = {}
        for cat_name in ['Analgesics', 'Antibiotics', 'Antimalarials', 'Gastrointestinal', 'Antihistamines', 'Cardiovascular', 'Dermatology']:
            category_map[cat_name], _ = MedicineCategory.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} medicines'}
            )

        suppliers = []
        for name, contact, email in ke.PHARMA_SUPPLIERS:
            phone = ke.phone()
            supplier, _ = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact,
                    'phone': phone,
                    'email': email,
                    'address': 'Nairobi, Kenya',
                },
            )
            suppliers.append(supplier)

        # First create medicines if not exist
        med_data = [
            ('Paracetamol 500mg', 'Paracetamol', 'Tablet', 'Analgesics', 3.50, 500),
            ('Amoxicillin 500mg', 'Amoxicillin', 'Capsule', 'Antibiotics', 10.00, 300),
            ('Omeprazole 20mg', 'Omeprazole', 'Capsule', 'Gastrointestinal', 8.00, 350),
            ('Cetirizine 10mg', 'Cetirizine', 'Tablet', 'Antihistamines', 3.00, 400),
            ('Metformin 500mg', 'Metformin', 'Tablet', 'Cardiovascular', 4.00, 400),
            ('Losartan 50mg', 'Losartan', 'Tablet', 'Cardiovascular', 8.50, 320),
            ('Atorvastatin 20mg', 'Atorvastatin', 'Tablet', 'Cardiovascular', 15.00, 200),
            ('Pantoprazole 40mg', 'Pantoprazole', 'Tablet', 'Gastrointestinal', 12.00, 280),
            ('Azithromycin 500mg', 'Azithromycin', 'Capsule', 'Antibiotics', 18.00, 250),
            ('Diclofenac Gel', 'Diclofenac', 'Ointment', 'Dermatology', 65.00, 150),
            ('Artemether/Lumefantrine 20/120mg', 'Artemether-Lumefantrine', 'Tablet', 'Antimalarials', 25.00, 400),
            ('ORS + Zinc Co-pack', 'Oral Rehydration Salts + Zinc', 'Tablet', 'Gastrointestinal', 40.00, 300),
        ]
        medicines = []
        for name, generic, cat, category_fk, price, stock in med_data:
            med, _ = Medicine.objects.get_or_create(
                name=name, defaults={
                    'generic_name': generic, 'category': cat,
                    'category_fk': category_map[category_fk],
                    'unit_price': Decimal(str(price)), 'stock_quantity': stock,
                    'minimum_stock': 50,
                    'expiry_date': date(random.choice([2027, 2028]), random.randint(1, 12), random.randint(1, 28)),
                    'batch_number': f'BATCH-{random.randint(1000,9999)}',
                    'manufacturer': random.choice(ke.MANUFACTURERS),
                }
            )
            if not med.category_fk:
                med.category_fk = category_map[category_fk]
                med.save()
            med.suppliers.add(*random.sample(suppliers, min(2, len(suppliers))))
            medicines.append(med)

        frequencies = ['Once Daily', 'Twice Daily', 'Three Times Daily', 'Every 8 Hours']
        durations = ['3 days', '5 days', '7 days', '10 days', '14 days', '30 days']

        completed_visits = list(Visit.objects.all())
        for i, visit in enumerate(completed_visits[:50]):
            doc_user = visit.appointment.doctor.user
            pat = visit.appointment.patient
            rx = Prescription.objects.create(
                visit=visit, doctor=doc_user, patient=pat,
                diagnosis=visit.diagnosis,
                notes='Take medicines as prescribed.',
                is_dispensed=random.random() > 0.4,
            )
            num_items = random.randint(1, 4)
            selected_meds = random.sample(medicines, min(num_items, len(medicines)))
            for med in selected_meds:
                PrescriptionItem.objects.create(
                    prescription=rx, medicine=med,
                    dosage=f'{random.choice([1, 2])} {med.category.lower()}',
                    frequency=random.choice(frequencies),
                    duration=random.choice(durations),
                    quantity=random.randint(10, 60),
                    instructions='Take after meals',
                )
            if rx.is_dispensed:
                total_cost = sum(
                    item.medicine.unit_price * item.quantity for item in rx.items.all()
                )
                DispensedMedicine.objects.create(
                    prescription=rx,
                    dispensed_by=random.choice(self.pharmacists) if self.pharmacists else doc_user,
                    total_cost=total_cost,
                )
        self.stdout.write('  Prescriptions created.')

    def _create_lab_data(self):
        from laboratory.models import LabTest, LabOrder, LabOrderItem, LabResult

        test_data = [
            ('Complete Blood Count (CBC)', 300, '4.5-11.0 x10^9/L', 'x10^9/L'),
            ('Blood Sugar (Fasting)', 150, '70-100 mg/dL', 'mg/dL'),
            ('Lipid Profile', 800, 'Total < 200 mg/dL', 'mg/dL'),
            ('Liver Function Test', 600, 'ALT 7-56 U/L', 'U/L'),
            ('Kidney Function Test', 500, 'Creatinine 0.7-1.3 mg/dL', 'mg/dL'),
            ('Thyroid Function Test', 700, 'TSH 0.4-4.0 mIU/L', 'mIU/L'),
            ('Urine Routine', 200, 'Normal', ''),
            ('HbA1c', 400, '< 5.7%', '%'),
            ('Vitamin D', 1200, '30-100 ng/mL', 'ng/mL'),
            ('ECG', 250, 'Normal sinus rhythm', ''),
        ]
        tests = []
        for name, price, normal_range, unit in test_data:
            test, _ = LabTest.objects.get_or_create(
                name=name, defaults={
                    'price': Decimal(str(price)),
                    'normal_range': normal_range, 'unit': unit,
                    'department': self.departments['Pathology'],
                }
            )
            tests.append(test)

        completed_appts = [a for a in self.appointments if a.status == 'Completed']
        for i in range(50):
            appt = random.choice(completed_appts) if completed_appts else None
            user_p, pat = random.choice(self.patients)
            doc_user, doc = random.choice(self.doctors)

            status = random.choices(
                ['Pending', 'In-Progress', 'Completed', 'Cancelled'],
                weights=[0.2, 0.1, 0.6, 0.1]
            )[0]

            order = LabOrder.objects.create(
                patient=pat, doctor=doc_user,
                appointment=appt,
                status=status,
                priority=random.choice(['Routine', 'Routine', 'Routine', 'Urgent']),
                completed_at=self.now - timedelta(days=random.randint(0, 30)) if status == 'Completed' else None,
            )
            selected_tests = random.sample(tests, random.randint(1, 3))
            for test in selected_tests:
                item = LabOrderItem.objects.create(order=order, test=test)
                if status == 'Completed':
                    result_val = str(round(random.uniform(50, 200), 1))
                    LabResult.objects.create(
                        order_item=item,
                        result_value=result_val,
                        reference_range=test.normal_range,
                        is_abnormal=random.random() > 0.8,
                        uploaded_by=random.choice(self.lab_techs) if self.lab_techs else doc_user,
                    )
        self.stdout.write('  Lab orders & results created.')

    def _create_radiology_data(self):
        from radiology.models import RadiologyTest, RadiologyOrder, RadiologyReport

        rad_tests = [
            ('X-Ray Chest', 500), ('X-Ray Spine', 600),
            ('CT Scan Head', 3000), ('CT Scan Abdomen', 4000),
            ('MRI Brain', 8000), ('MRI Spine', 8500),
            ('Ultrasound Abdomen', 1500), ('Ultrasound Pelvis', 1500),
            ('Mammography', 2000), ('Echocardiogram', 2500),
        ]
        rad_test_objs = []
        for name, price in rad_tests:
            test, _ = RadiologyTest.objects.get_or_create(
                name=name, defaults={'price': Decimal(str(price))}
            )
            rad_test_objs.append(test)

        for i in range(30):
            user_p, pat = random.choice(self.patients)
            doc_user, doc = random.choice(self.doctors)
            test = random.choice(rad_test_objs)
            status = random.choices(
                ['Pending', 'In-Progress', 'Completed'],
                weights=[0.3, 0.1, 0.6]
            )[0]

            order = RadiologyOrder.objects.create(
                patient=pat, doctor=doc_user, test=test,
                clinical_information='Patient presents with symptoms requiring imaging.',
                status=status,
                priority=random.choice(['Routine', 'Routine', 'Urgent']),
                completed_at=self.now - timedelta(days=random.randint(0, 30)) if status == 'Completed' else None,
            )
            if status == 'Completed':
                RadiologyReport.objects.create(
                    order=order,
                    findings='No significant abnormality detected.',
                    impression='Normal study.',
                    reported_by=doc_user,
                )
        self.stdout.write('  Radiology orders & reports created.')

    def _create_billing(self):
        from billing.models import Invoice, InvoiceItem, Payment
        item_descriptions = [
            ('Consultation Fee', 1, 700),
            ('ECG', 1, 250),
            ('Blood Test - CBC', 1, 300),
            ('X-Ray', 1, 500),
            ('Medicine Charges', 1, 450),
            ('Procedure Fee', 1, 1500),
            ('Room Charges (per day)', 1, 2000),
            ('Injection Fee', 1, 100),
            ('Dressing', 1, 200),
            ('Physiotherapy Session', 1, 800),
        ]
        payment_methods = ke.PAYMENT_METHODS

        # Create invoices spread across last 60 days
        for day_offset in range(-60, 1):
            inv_date = self.today + timedelta(days=day_offset)
            num_invoices = random.randint(1, 4)
            for _ in range(num_invoices):
                user_p, pat = random.choice(self.patients)
                appt = random.choice(self.appointments) if self.appointments else None

                status = random.choices(
                    ['Paid', 'Paid', 'Partial', 'Pending'],
                    weights=[0.4, 0.2, 0.15, 0.25]
                )[0]

                discount = Decimal(str(random.choice([0, 0, 0, 100, 200, 500])))
                tax = Decimal(str(random.randint(0, 200)))

                invoice = Invoice(
                    patient=pat, appointment=appt,
                    discount=discount, tax=tax,
                    status=status,
                    created_by=self.admin_user,
                )
                invoice.save()

                # Force created_at to the desired date
                Invoice.objects.filter(pk=invoice.pk).update(created_at=timezone.make_aware(datetime.combine(inv_date, time(random.randint(8, 18), random.randint(0, 59)))))

                total = Decimal('0')
                num_items = random.randint(1, 4)
                selected_items = random.sample(item_descriptions, num_items)
                for desc, qty, price in selected_items:
                    item_total = Decimal(str(qty * price))
                    InvoiceItem.objects.create(
                        invoice=invoice, description=desc,
                        quantity=qty, unit_price=Decimal(str(price)),
                        total_price=item_total,
                    )
                    total += item_total

                invoice.total_amount = total
                invoice.save()

                if status == 'Paid':
                    Payment.objects.create(
                        invoice=invoice,
                        amount=invoice.net_amount,
                        **ke.payment(payment_methods),
                        received_by=self.admin_user,
                    )
                elif status == 'Partial':
                    partial = invoice.net_amount * Decimal('0.5')
                    Payment.objects.create(
                        invoice=invoice,
                        amount=partial,
                        **ke.payment(payment_methods),
                        received_by=self.admin_user,
                    )
        self.stdout.write('  Invoices & payments created.')

    def _create_ipd(self):
        from ipd.models import Ward, Bed, Admission

        ward_data = [
            ('General Ward A', 'General', 1, 20),
            ('General Ward B', 'General', 1, 15),
            ('ICU', 'ICU', 2, 8),
            ('CCU', 'CCU', 2, 6),
            ('Private Ward', 'Private', 3, 10),
            ('Semi-Private Ward', 'Semi-Private', 3, 12),
        ]
        self.wards = {}
        for name, wtype, floor, cap in ward_data:
            dept = random.choice([self.departments['General Medicine'], self.departments['Cardiology']])
            ward = Ward.objects.create(
                name=name, department=dept, floor=floor,
                capacity=cap, ward_type=wtype,
            )
            for j in range(1, cap + 1):
                Bed.objects.create(
                    ward=ward, bed_number=f'{name[:3].upper()}-{j}',
                    bed_type='Normal' if wtype not in ['ICU', 'CCU'] else 'Ventilator',
                    daily_rate=Decimal(str(random.choice([500, 800, 1000, 1500, 2000, 2500]))),
                )
            self.wards[name] = ward

        # Create some admissions
        for i in range(8):
            user_p, pat = random.choice(self.patients)
            doc_user, doc = random.choice(self.doctors)
            ward = random.choice(list(self.wards.values()))
            bed = ward.beds.filter(status='Available').first()
            if bed:
                Admission.objects.create(
                    patient=pat, doctor=doc,
                    admission_type=random.choice(['Emergency', 'Elective']),
                    ward=ward, bed=bed,
                    diagnosis=random.choice([
                        'Acute MI', 'Stroke', 'Pneumonia', 'Fracture',
                        'Appendicitis', 'Diabetic ketoacidosis',
                    ]),
                    status='Admitted',
                )
        self.stdout.write('  Wards & beds created.')

    def _create_nursing(self):
        from nursing.models import NursingStation, NursingTask, VitalSigns

        station_names = ['Station A - General', 'Station B - ICU', 'Station C - Private']
        for name in station_names:
            ward = random.choice(list(self.wards.values()))
            nurse = random.choice(self.nurses) if self.nurses else None
            NursingStation.objects.create(
                name=name, ward=ward, capacity=10,
                nurse_in_charge=nurse,
            )

        for i in range(20):
            user_p, pat = random.choice(self.patients)
            task_type = random.choice(['Medication', 'Vitals', 'Wound Care', 'IV', 'Other'])
            status = random.choices(
                ['Pending', 'In-Progress', 'Completed', 'Skipped'],
                weights=[0.3, 0.1, 0.5, 0.1]
            )[0]
            NursingTask.objects.create(
                patient=pat,
                assigned_to=random.choice(self.nurses) if self.nurses else self.admin_user,
                task_type=task_type,
                description=f'{task_type} task for patient',
                scheduled_time=self.now - timedelta(days=random.randint(0, 7), hours=random.randint(0, 12)),
                status=status,
                completed_at=self.now if status == 'Completed' else None,
            )

        # Create vital signs
        for i in range(15):
            user_p, pat = random.choice(self.patients)
            VitalSigns.objects.create(
                patient=pat,
                recorded_by=random.choice(self.nurses) if self.nurses else self.admin_user,
                temperature=Decimal(str(round(random.uniform(97.0, 102.0), 1))),
                blood_pressure_systolic=random.randint(100, 160),
                blood_pressure_diastolic=random.randint(60, 100),
                heart_rate=random.randint(60, 100),
                respiratory_rate=random.randint(12, 24),
                oxygen_saturation=Decimal(str(round(random.uniform(94.0, 99.0), 1))),
                weight=Decimal(str(round(random.uniform(45.0, 90.0), 2))),
            )
        self.stdout.write('  Nursing stations & tasks created.')

    def _create_ambulance(self):
        from ambulance.models import Ambulance, AmbulanceRequest

        ambulances = [
            ('KDJ 101A', 'Basic', 'Joseph Kamau', ke.phone()),
            ('KDK 202B', 'AC', 'Hassan Juma', ke.phone()),
            ('KDL 303C', 'ICU', 'Peter Otieno', ke.phone()),
        ]
        amb_objs = []
        for vnum, vtype, driver, phone in ambulances:
            amb = Ambulance.objects.create(
                vehicle_number=vnum, vehicle_type=vtype,
                driver_name=driver, driver_phone=phone,
                current_location='MEDCARE Hospital',
            )
            amb_objs.append(amb)

        locations = [
            ('Westlands', 'Kilimani'), ('Lavington', 'Kasarani'),
            ('Karen', 'CBD'), ('South B', 'Embakasi'),
        ]
        for i in range(10):
            pickup, dropoff = random.choice(locations)
            AmbulanceRequest.objects.create(
                patient_name=f'Emergency Patient {i+1}',
                patient_phone=ke.phone(),
                pickup_location=f'{pickup}, Nairobi',
                dropoff_location=f'MEDCARE Hospital, {dropoff}',
                ambulance=random.choice(amb_objs),
                status=random.choice(['Pending', 'Dispatched', 'In-Transit', 'Completed']),
                requested_by=self.admin_user,
                distance_km=Decimal(str(round(random.uniform(2.0, 15.0), 1))),
            )
        self.stdout.write('  Ambulance created.')

    def _create_inventory(self):
        from inventory.models import InventoryCategory, InventoryItem, PurchaseOrder

        categories = {
            'Medical Equipment': [
                ('Stethoscope', 'Equipment', 10, 'pcs', 1500),
                ('BP Monitor', 'Equipment', 15, 'pcs', 2500),
                ('Thermometer', 'Equipment', 30, 'pcs', 500),
                ('Pulse Oximeter', 'Equipment', 20, 'pcs', 1200),
            ],
            'Consumables': [
                ('Syringes', 'Consumable', 500, 'pcs', 5),
                ('Gloves', 'Consumable', 1000, 'boxes', 150),
                ('Bandages', 'Consumable', 200, 'rolls', 30),
                ('Cotton Rolls', 'Consumable', 150, 'rolls', 25),
            ],
            'Surgical Supplies': [
                ('Surgical Masks', 'Supplies', 500, 'boxes', 100),
                ('Gowns', 'Supplies', 100, 'pcs', 200),
                ('Scalpel Blades', 'Supplies', 300, 'pcs', 15),
            ],
        }
        self.inv_items = []
        for cat_name, items in categories.items():
            cat, _ = InventoryCategory.objects.get_or_create(name=cat_name)
            for item_name, item_type, qty, unit, price in items:
                item = InventoryItem.objects.create(
                    name=item_name, category=cat,
                    item_type=item_type, quantity=qty,
                    unit=unit, unit_price=Decimal(str(price)),
                    reorder_level=20,
                    location=f'Warehouse {random.choice(["A", "B", "C"])}',
                )
                self.inv_items.append(item)

        # Create purchase orders
        for i in range(8):
            item = random.choice(self.inv_items)
            PurchaseOrder.objects.create(
                item=item,
                supplier_name=f'Supplier {random.choice(["A", "B", "C"])}',
                quantity=random.randint(50, 200),
                total_cost=Decimal(str(random.randint(5000, 50000))),
                order_date=self.today - timedelta(days=random.randint(0, 30)),
                expected_delivery=self.today + timedelta(days=random.randint(5, 15)),
                status=random.choice(['Pending', 'Ordered', 'Delivered']),
                ordered_by=self.admin_user,
            )
        self.stdout.write('  Inventory created.')

    def _create_hr(self):
        from hr.models import Designation, HRRecord, Training
        from employees.models import Employee, Attendance, LeaveRequest

        designations = [
            'Senior Consultant', 'Junior Consultant', 'Staff Nurse',
            'Pharmacist', 'Lab Technician', 'Accountant',
            'Receptionist', 'Ward Boy', 'Sweeper',
        ]
        for name in designations:
            Designation.objects.create(name=name, department=random.choice(list(self.departments.values())))

        employees = list(Employee.objects.all())
        for emp in employees[:10]:
            HRRecord.objects.create(
                employee=emp,
                record_type=random.choice(['Appointment', 'Promotion', 'Increment']),
                effective_date=self.today - timedelta(days=random.randint(30, 365)),
                description=f'{emp.designation} - HR record',
                created_by=self.admin_user,
            )

        Training.objects.create(
            title='Hospital Safety Training',
            description='Annual safety and emergency training',
            trainer='Dr. Safety Officer',
            start_date=self.today - timedelta(days=10),
            end_date=self.today + timedelta(days=20),
            status='Ongoing',
        ).employees.add(*employees[:12])

        Training.objects.create(
            title='Infection Control Workshop',
            description='Hand hygiene, PPE, isolation protocol, and waste management workshop',
            trainer='Nurse Educator Grace Wambui',
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=7),
            status='Planned',
        ).employees.add(*employees[5:18])

        Training.objects.create(
            title='Emergency Response Drill',
            description='Code blue response, triage, and evacuation drill',
            trainer='Emergency Coordinator',
            start_date=self.today - timedelta(days=30),
            end_date=self.today - timedelta(days=28),
            status='Completed',
        ).employees.add(*employees[:20])

        # Attendance
        for emp in employees[:15]:
            for day_offset in range(-7, 1):
                att_date = self.today + timedelta(days=day_offset)
                if att_date.weekday() < 6:  # Mon-Sat
                    Attendance.objects.create(
                        employee=emp, date=att_date,
                        check_in=time(random.randint(8, 9), random.randint(0, 30)),
                        check_out=time(random.randint(17, 18), random.randint(0, 30)),
                        status=random.choice(['Present', 'Present', 'Present', 'Late', 'Absent']),
                    )

        # Leave requests
        for emp in employees[:8]:
            LeaveRequest.objects.create(
                employee=emp,
                leave_type=random.choice(['Sick', 'Casual', 'Earned']),
                start_date=self.today + timedelta(days=random.randint(1, 30)),
                end_date=self.today + timedelta(days=random.randint(3, 35)),
                reason='Personal reasons',
                status=random.choice(['Pending', 'Approved', 'Rejected']),
                approved_by=self.admin_user if random.random() > 0.5 else None,
            )
        self.stdout.write('  HR records created.')

    def _create_notifications(self):
        from notifications.models import Notification

        notif_types = ['Appointment', 'Billing', 'Laboratory', 'Pharmacy', 'General', 'Alert']
        titles = [
            'Appointment Confirmed', 'Payment Received', 'Lab Results Ready',
            'Prescription Dispensed', 'System Update', 'Low Stock Alert',
            'New Admission', 'Leave Approved', 'Training Reminder',
            'Invoice Generated',
        ]
        messages = [
            'Your appointment has been confirmed for tomorrow.',
            'Payment of KSh 1500 has been received successfully.',
            'Your lab results are ready for collection.',
            'Your prescription has been dispensed.',
            'System maintenance scheduled for this weekend.',
            'Medicine stock is running low for Paracetamol.',
            'New patient admitted to ICU Ward.',
            'Your leave request has been approved.',
            'Training session starts next week.',
            'Invoice #INV-001 has been generated.',
        ]
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            for i in range(10):
                Notification.objects.create(
                    recipient=admin_user,
                    sender=admin_user,
                    title=titles[i],
                    message=messages[i],
                    notification_type=random.choice(notif_types),
                    is_read=random.random() > 0.6,
                    link='/dashboard/',
                )
        self.stdout.write('  Notifications created.')

    def _create_audit_logs(self):
        from auditlogs.models import AuditLog

        actions = ['Login', 'Create', 'Update', 'View']
        models = ['Appointment', 'Patient', 'Invoice', 'Medicine', 'LabOrder']
        for i in range(30):
            AuditLog.objects.create(
                user=self.admin_user,
                action=random.choice(actions),
                model_name=random.choice(models),
                object_id=str(random.randint(1, 100)),
                description=f'{random.choice(actions)} on {random.choice(models)}',
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                path=f'/admin/{random.choice(models).lower()}/',
                method=random.choice(['GET', 'POST']),
            )
        self.stdout.write('  Audit logs created.')

    def _print_summary(self):
        from accounts.models import User
        from patients.models import Patient
        from appointments.models import Appointment
        from billing.models import Invoice
        from laboratory.models import LabOrder
        from pharmacy.models import Prescription

        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write('  SEED DATA SUMMARY')
        self.stdout.write('=' * 50)
        self.stdout.write(f'  Users:          {User.objects.count()}')
        self.stdout.write(f'  Patients:       {Patient.objects.count()}')
        self.stdout.write(f'  Doctors:        {User.objects.filter(roles__name="Doctor").distinct().count()}')
        self.stdout.write(f'  Appointments:   {Appointment.objects.count()}')
        self.stdout.write(f'  Today Appts:    {Appointment.objects.filter(appointment_date=self.today).count()}')
        self.stdout.write(f'  Prescriptions:  {Prescription.objects.count()}')
        self.stdout.write(f'  Lab Orders:     {LabOrder.objects.count()}')
        self.stdout.write(f'  Invoices:       {Invoice.objects.count()}')
        self.stdout.write('=' * 50)
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Admin:        admin / admin123')
        self.stdout.write('  Doctor:       dr.wanjiku.kamau / doctor123')
        self.stdout.write('  Patient:      patient.zawadi.njoroge / patient123')
        self.stdout.write('  Nurse:        nurse.grace.wambui / nurse123')
        self.stdout.write('  Pharmacist:   pharmacist.collins / pharmacist123')
        self.stdout.write('  Lab Tech:     labtech.dennis / lab123')
        self.stdout.write('  Accountant:   accountant.kevin / accountant123')
        self.stdout.write('  Receptionist: receptionist.victor / receptionist123')
        self.stdout.write('')
        self.stdout.write('Run: python manage.py migrate && python manage.py runserver')
