import random
from datetime import date, time, timedelta, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from core import seed_kenya as ke
from django.db import transaction
from django.utils import timezone

from accounts.models import User, Role
from hospitals.models import Branch
from departments.models import Department, Specialization
from employees.models import Employee, Attendance, LeaveRequest
from doctors.models import Doctor, DoctorSchedule, DoctorAvailability
from patients.models import Patient, MedicalRecord
from appointments.models import Appointment, Visit
from opd.models import OPDVisit
from ipd.models import Ward, Bed, Admission
from pharmacy.models import MedicineCategory, Supplier, Medicine, Prescription, PrescriptionItem, DispensedMedicine
from laboratory.models import LabTest, LabOrder, LabOrderItem, LabResult
from radiology.models import RadiologyTest, RadiologyOrder, RadiologyReport
from billing.models import Invoice, InvoiceItem, Payment
from insurance.models import InsuranceProvider, InsurancePlan, PatientInsurance
from nursing.models import NursingStation, NursingTask, VitalSigns
from ambulance.models import Ambulance, AmbulanceRequest
from inventory.models import InventoryCategory, InventoryItem, PurchaseOrder
from hr.models import Designation, HRRecord, Training
from auditlogs.models import AuditLog
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Clear all data and create fresh comprehensive demo seed data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Clearing all existing data...'))
        with transaction.atomic():
            self._clear_data()

        self.stdout.write(self.style.SUCCESS('Creating seed data...'))
        with transaction.atomic():
            self._create_seed_data()

        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully!'))
        self.stdout.write(self.style.SUCCESS('Login: admin / admin123'))

    def _clear_data(self):
        models_to_clear = [
            AuditLog, Notification, Training, HRRecord, Designation,
            PurchaseOrder, InventoryItem, InventoryCategory,
            AmbulanceRequest, Ambulance,
            VitalSigns, NursingTask, NursingStation,
            Payment, InvoiceItem, Invoice,
            RadiologyReport, RadiologyOrder, RadiologyTest,
            LabResult, LabOrderItem, LabOrder, LabTest,
            DispensedMedicine, PrescriptionItem, Prescription,
            Medicine, Supplier, MedicineCategory,
            Admission, Bed, Ward,
            OPDVisit, Visit, Appointment,
            MedicalRecord, Patient,
            DoctorSchedule, DoctorAvailability, Doctor,
            Attendance, LeaveRequest, Employee,
            Specialization, Department,
            Branch,
            PatientInsurance, InsurancePlan, InsuranceProvider,
        ]
        for model in models_to_clear:
            model.objects.all().delete()

        User.objects.all().delete()
        Role.objects.all().delete()
        self.stdout.write('  All data cleared.')

    def _create_seed_data(self):
        # 1. Roles
        role_names = [
            'Super Admin', 'Hospital Admin', 'Doctor', 'Nurse',
            'Patient', 'Pharmacist', 'Lab Technician', 'Accountant',
            'HR Manager', 'Receptionist', 'Radiologist',
        ]
        roles = {}
        for name in role_names:
            roles[name] = Role.objects.create(name=name, description=f'{name} role')
        self.stdout.write('  Roles created.')

        # 2. Superuser
        admin = User.objects.create_superuser(
            username='admin', email='admin@medcare.co.ke', password='admin123',
            first_name='System', last_name='Administrator',
            phone='+254700000000', gender='Male',
        )
        admin.roles.add(roles['Super Admin'])
        self.stdout.write('  Admin user created.')

        # 3. Branch
        branch = Branch.objects.create(
            name='Main Branch',
            address='45 Medical Road, Westlands, Nairobi',
            phone='+254725500100', is_main_branch=True,
        )
        self.stdout.write('  Branch created.')

        # 4. Departments
        dept_data = [
            ('Cardiology', 'Heart and cardiovascular system'),
            ('Neurology', 'Brain and nervous system'),
            ('Orthopedics', 'Bones, joints, and muscles'),
            ('Pediatrics', 'Children health'),
            ('Radiology', 'Medical imaging'),
            ('Pathology', 'Laboratory diagnostics'),
            ('Emergency Medicine', 'Emergency and trauma care'),
            ('General Medicine', 'General health and wellness'),
            ('Surgery', 'Surgical procedures'),
            ('Pharmacy', 'Medicine dispensing'),
            ('Oncology', 'Cancer treatment'),
            ('Dermatology', 'Skin conditions'),
            ('ENT', 'Ear, nose, and throat'),
            ('Gynecology', 'Women reproductive health'),
        ]
        departments = {}
        for name, desc in dept_data:
            departments[name] = Department.objects.create(
                name=name, branch=branch,
                phone=ke.landline(),
                email=f'{name.lower().replace(" ",".")}@medcare.co.ke',
            )
        self.stdout.write('  Departments created.')

        # 5. Specializations
        spec_data = {
            'Cardiology': ['Interventional Cardiology', 'Electrophysiology', 'Cardiac Surgery'],
            'Neurology': ['Stroke Medicine', 'Epilepsy', 'Neuromuscular Medicine'],
            'Orthopedics': ['Spine Surgery', 'Joint Replacement', 'Sports Medicine'],
            'Pediatrics': ['Neonatology', 'Child Development'],
            'General Medicine': ['Internal Medicine', 'Family Medicine'],
            'Surgery': ['General Surgery', 'Laparoscopic Surgery'],
            'Oncology': ['Medical Oncology', 'Radiation Oncology'],
            'Dermatology': ['Cosmetic Dermatology', 'Pediatric Dermatology'],
            'ENT': ['Otorhinolaryngology', 'Head and Neck Surgery'],
            'Gynecology': ['Obstetrics', 'Reproductive Endocrinology'],
        }
        specializations = {}
        for dept_name, specs in spec_data.items():
            for spec_name in specs:
                specializations[spec_name] = Specialization.objects.create(
                    name=spec_name, department=departments[dept_name],
                )
        self.stdout.write('  Specializations created.')

        # 6. Doctors
        doctor_data = [
            ('Abdi', 'Abdullahi', 'Male', 'Cardiology', 'Interventional Cardiology', 55000, 15, 2000),
            ('Jepkosgei', 'Odhiambo', 'Female', 'Neurology', 'Stroke Medicine', 60000, 12, 2500),
            ('Mwangi', 'Omondi', 'Male', 'Orthopedics', 'Spine Surgery', 50000, 10, 1800),
            ('Zawadi', 'Gitau', 'Female', 'Pediatrics', 'Neonatology', 45000, 8, 1500),
            ('Juma', 'Kirui', 'Male', 'General Medicine', 'Internal Medicine', 40000, 5, 1000),
            ('Kerubo', 'Kariuki', 'Female', 'Surgery', 'General Surgery', 55000, 7, 2200),
            ('Moses', 'Kimani', 'Male', 'Cardiology', 'Electrophysiology', 48000, 6, 1800),
            ('Achieng', 'Kiprotich', 'Female', 'Neurology', 'Epilepsy', 52000, 9, 2000),
            ('Elijah', 'Barasa', 'Male', 'Orthopedics', 'Joint Replacement', 47000, 4, 1600),
            ('Kemunto', 'Kamau', 'Female', 'General Medicine', 'Family Medicine', 38000, 3, 1000),
            ('David', 'Ochieng', 'Male', 'Pediatrics', 'Child Development', 42000, 6, 1400),
            ('Patrick', 'Kiplagat', 'Male', 'Neurology', 'Neuromuscular Medicine', 51000, 8, 1900),
            ('Gitonga', 'Abdullahi', 'Male', 'Cardiology', 'Cardiac Surgery', 65000, 18, 3000),
            ('Kioko', 'Kiprotich', 'Male', 'Oncology', 'Medical Oncology', 53000, 11, 2100),
            ('Muthoni', 'ara', 'Female', 'Dermatology', 'Cosmetic Dermatology', 35000, 4, 1200),
        ]
        doctors = []
        for i, (first, last, gender, dept, spec, salary, exp, fee) in enumerate(doctor_data):
            user = User.objects.create_user(
                username=f'doctor.{first.lower()}.{last.lower()}',
                email=f'{first.lower()}.{last.lower()}@medcare.co.ke',
                password='doctor123',
                first_name=first, last_name=last,
                phone=ke.phone(),
                gender=gender, date_of_birth=date(1970+i, 1, 15),
            )
            user.roles.add(roles['Doctor'])
            emp = Employee.objects.create(
                user=user, department=departments[dept],
                designation='Senior Doctor' if exp > 7 else 'Doctor',
                date_of_joining=date(2020, 1, 1),
                salary=Decimal(str(salary)),
            )
            doc = Doctor.objects.create(
                employee=emp,
                specialization=specializations.get(spec),
                consultation_fee=Decimal(str(fee)),
                years_of_experience=exp,
                bio=f'Dr. {first} {last} - {spec} specialist with {exp} years of experience.',
            )
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            for day in days[:random.randint(3, 5)]:
                DoctorSchedule.objects.create(
                    doctor=doc, day_of_week=day,
                    start_time=time(9, 0), end_time=time(17, 0),
                )
            avail_dates = set()
            for j in range(random.randint(2, 4)):
                while True:
                    d = date.today() + timedelta(days=random.randint(1, 30))
                    if d not in avail_dates:
                        avail_dates.add(d)
                        break
                DoctorAvailability.objects.get_or_create(
                    doctor=doc, date=d, start_time=time(9, 0),
                    defaults={'end_time': time(13, 0), 'max_patients': 20},
                )
            doctors.append((user, doc))
        self.stdout.write('  Doctors created.')

        # 7. Nurses
        nurse_data = [
            ('Chepkoech', 'Nyambura'), ('Nekesa', 'Odhiambo'), ('Moraa', 'Kimani'),
            ('Muthoni', 'Kariuki'), ('Lilian', 'Odhiambo'),
        ]
        nurse_users = []
        for first, last in nurse_data:
            user = User.objects.create_user(
                username=f'nurse.{first.lower()}.{last.lower()}',
                email=f'{first.lower()}.{last.lower()}@medcare.co.ke',
                password='nurse123',
                first_name=first, last_name=last,
                phone=ke.phone(),
                gender='Female', date_of_birth=date(1985, 5, 10),
            )
            user.roles.add(roles['Nurse'])
            Employee.objects.create(
                user=user, department=departments['General Medicine'],
                designation='Nurse', date_of_joining=date(2021, 6, 1),
                salary=Decimal('25000'),
            )
            nurse_users.append(user)
        self.stdout.write('  Nurses created.')

        # 8. Pharmacists
        pharmacist_users = []
        for first, last in [('Kimutai', 'Noor'), ('Faith', 'Nzioka')]:
            user = User.objects.create_user(
                username=f'pharm.{first.lower()}.{last.lower()}',
                email=f'{first.lower()}.{last.lower()}@medcare.co.ke',
                password='pharm123',
                first_name=first, last_name=last,
                phone=ke.phone(),
                gender='Male' if first == 'Kimutai' else 'Female',
            )
            user.roles.add(roles['Pharmacist'])
            Employee.objects.create(
                user=user, department=departments['Pharmacy'],
                designation='Pharmacist', date_of_joining=date(2021, 3, 1),
                salary=Decimal('28000'),
            )
            pharmacist_users.append(user)
        self.stdout.write('  Pharmacists created.')

        # 9. Lab Technicians
        lab_tech_users = []
        for first, last in [('Swaleh', 'Keter'), ('Esther', 'Were')]:
            user = User.objects.create_user(
                username=f'lab.{first.lower()}.{last.lower()}',
                email=f'{first.lower()}.{last.lower()}@medcare.co.ke',
                password='lab123',
                first_name=first, last_name=last,
                phone=ke.phone(),
                gender='Male' if first == 'Swaleh' else 'Female',
            )
            user.roles.add(roles['Lab Technician'])
            Employee.objects.create(
                user=user, department=departments['Pathology'],
                designation='Lab Technician', date_of_joining=date(2022, 1, 1),
                salary=Decimal('22000'),
            )
            lab_tech_users.append(user)
        self.stdout.write('  Lab Technicians created.')

        # 10. Accountant
        acc_user = User.objects.create_user(
            username='accountant.tanim', email='tanim@medcare.co.ke', password='acc123',
            first_name='Patrick', last_name='Omondi',
            phone='+254730593240', gender='Male',
        )
        acc_user.roles.add(roles['Accountant'])
        Employee.objects.create(
            user=acc_user, department=departments['General Medicine'],
            designation='Accountant', date_of_joining=date(2022, 6, 1),
            salary=Decimal('30000'),
        )

        # 11. HR Manager
        hr_user = User.objects.create_user(
            username='hr.hasan', email='hasan@medcare.co.ke', password='hr123',
            first_name='Muli', last_name='Barasa',
            phone='+254755000000', gender='Male',
        )
        hr_user.roles.add(roles['HR Manager'])
        Employee.objects.create(
            user=hr_user, department=departments['General Medicine'],
            designation='HR Manager', date_of_joining=date(2021, 1, 1),
            salary=Decimal('35000'),
        )
        self.stdout.write('  Support staff created.')

        all_staff = [u for u, d in doctors] + nurse_users + pharmacist_users + lab_tech_users + [acc_user, hr_user]

        # 12. Insurance
        ip1 = InsuranceProvider.objects.create(
            name='Jubilee Health Insurance', contact_person='Wanjala',
            phone='+254729876543', email='info@jubilee.example.com',
        )
        ip2 = InsuranceProvider.objects.create(
            name='AAR Insurance Kenya', contact_person='Nisa',
            phone='+254729876000', email='info@aar.example.com',
        )
        ip3 = InsuranceProvider.objects.create(
            name='Britam', contact_person='Juma',
            phone='+254729876111', email='info@britam.example.com',
        )
        plan1 = InsurancePlan.objects.create(
            provider=ip1, name='Gold Plan', coverage_percentage=70,
            max_coverage=Decimal('500000'), description='Premium full coverage',
        )
        plan2 = InsurancePlan.objects.create(
            provider=ip2, name='Silver Plan', coverage_percentage=50,
            max_coverage=Decimal('200000'), description='Standard coverage',
        )
        plan3 = InsurancePlan.objects.create(
            provider=ip3, name='Bronze Plan', coverage_percentage=30,
            max_coverage=Decimal('100000'), description='Basic coverage',
        )
        self.stdout.write('  Insurance created.')

        # 13. Patients
        patient_data = [
            ('Ndanu', 'Cheruiyot', 'Female', 'A+', 24),
            ('Mwende', 'Wekesa', 'Female', 'B+', 28),
            ('Mwende', 'Ali', 'Female', 'O-', 35),
            ('William', 'Kirui', 'Male', 'AB+', 45),
            ('Kagendo', 'Maina', 'Female', 'A-', 30),
            ('Kagendo', 'Kiplagat', 'Female', 'B-', 22),
            ('Eric', 'Wambua', 'Male', 'O+', 50),
            ('Chepkoech', 'Langat', 'Female', 'A+', 27),
            ('Eric', 'Kiplagat', 'Male', 'B+', 33),
            ('Patrick', 'Kirui', 'Male', 'AB-', 40),
            ('Omar', 'Barasa', 'Male', 'O+', 29),
            ('Caroline', 'Kimani', 'Female', 'A+', 31),
            ('Collins', 'Muriuki', 'Male', 'B-', 48),
            ('Kerubo', 'Korir', 'Female', 'O+', 26),
            ('Mugo', 'Keter', 'Male', 'AB+', 38),
            ('Lilian', 'Koech', 'Female', 'B+', 32),
            ('Harper', 'Cheruiyot', 'Male', 'A+', 41),
            ('Elizabeth', 'Ndungu', 'Female', 'O+', 55),
            ('Lily', 'Odhiambo', 'Female', 'AB+', 23),
            ('Chloe', 'Wekesa', 'Female', 'O+', 29),
            ('Atieno', 'Njoroge', 'Female', 'A-', 44),
            ('Muli', 'Keter', 'Male', 'B+', 37),
            ('Anyango', 'Nyambura', 'Female', 'O-', 25),
            ('Okoth', 'Abdullahi', 'Male', 'A+', 52),
            ('Kawira', 'Gitau', 'Female', 'B-', 30),
            ('Victor', 'Omondi', 'Male', 'AB+', 47),
            ('Zawadi', 'Bett', 'Female', 'A+', 22),
            ('Mohamed', 'Kimani', 'Male', 'O+', 39),
            ('Awino', 'Wambua', 'Female', 'B+', 34),
            ('Peter', 'Wanjala', 'Male', 'A-', 58),
            ('Akinyi', 'Okello', 'Female', 'AB-', 28),
            ('Francis', 'Omondi', 'Male', 'B+', 42),
            ('Esther', 'Kinyua', 'Female', 'O+', 31),
            ('Omondi', 'Ndungu', 'Male', 'A+', 46),
            ('Fatuma', 'Odhiambo', 'Female', 'B-', 36),
            ('Kamau', 'Wanjala', 'Male', 'O-', 53),
            ('Moraa', 'Kirui', 'Female', 'A+', 27),
            ('Rashid', 'Muriuki', 'Male', 'AB+', 40),
            ('Wanjiku', 'Kiprotich', 'Female', 'B+', 24),
            ('Ouma', 'Onyango', 'Male', 'O+', 49),
            ('Syokau', 'Mwangi', 'Female', 'A-', 33),
            ('Allan', 'Barasa', 'Male', 'B-', 41),
            ('Jebet', 'Kariuki', 'Female', 'AB-', 29),
            ('Waweru', 'Wafula', 'Male', 'O+', 38),
            ('Purity', 'Mwende', 'Female', 'A+', 26),
            ('Owino', 'Hassan', 'Male', 'B+', 44),
            ('Adhiambo', 'Gitau', 'Female', 'A+', 32),
            ('Dennis', 'Abdullahi', 'Male', 'O-', 56),
            ('Naliaka', 'Odhiambo', 'Female', 'B+', 23),
            ('Stephen', 'Noor', 'Male', 'AB+', 35),
        ]
        patients = []
        today = timezone.now().date()
        insurance_plans = [plan1, plan2, plan3]
        for i, (first, last, gender, blood, age) in enumerate(patient_data):
            year = 2026 - age
            user = User.objects.create_user(
                username=f'patient.{first.lower()}.{last.lower()}',
                email=f'{first.lower()}.{last.lower()}@email.com',
                password='patient123',
                first_name=first, last_name=last,
                phone=ke.phone(),
                gender=gender, date_of_birth=date(year, random.randint(1, 12), random.randint(1, 28)),
                address=f'{random.randint(1,200)} {random.choice(["Road","Lane","Avenue"])} {random.choice(["Westlands","Kilimani","Lavington","Kasarani","Karen"])}, Nairobi',
            )
            user.roles.add(roles['Patient'])

            pat_insurance_plan = insurance_plans[i % len(insurance_plans)] if random.random() > 0.3 else None
            pat = Patient.objects.create(
                user=user, blood_group=blood,
                emergency_contact_name=f'{last} Family',
                emergency_contact_phone=ke.phone(),
                insurance_provider=pat_insurance_plan,
            )

            # Also create PatientInsurance records for realistic data
            if pat_insurance_plan and random.random() > 0.2:
                policy_num = f'{ip1.name[:2].upper()}-2026-{str(i+1).zfill(3)}' if pat_insurance_plan == plan1 else \
                             f'{ip2.name[:4].upper()}-2026-{str(i+1).zfill(3)}' if pat_insurance_plan == plan2 else \
                             f'{ip3.name[:3].upper()}-2026-{str(i+1).zfill(3)}'
                PatientInsurance.objects.create(
                    patient=pat, plan=pat_insurance_plan,
                    policy_number=policy_num,
                    start_date=today - timedelta(days=random.randint(0, 60)),
                    end_date=today + timedelta(days=random.randint(180, 365)),
                )
            patients.append((user, pat))
        self.stdout.write('  Patients created.')

        # 14. Appointments & OPD
        statuses = ['Scheduled', 'Confirmed', 'In-Progress', 'Completed', 'Cancelled']
        appt_per_patient = 2
        for i, (user_p, pat) in enumerate(patients):
            for j in range(appt_per_patient):
                if Appointment.objects.count() >= 100:
                    break
                doc_user, doc = doctors[(i + j) % len(doctors)]
                appt_status = random.choice(statuses)
                appt = Appointment.objects.create(
                    patient=pat, doctor=doc,
                    appointment_date=today - timedelta(days=random.randint(0, 30)),
                    appointment_time=time(random.randint(9, 16), random.choice([0, 30])),
                    department=doc.employee.department,
                    status=appt_status,
                    reason=random.choice([
                        'General checkup', 'Follow-up visit', 'Chest pain',
                        'Headache consultation', 'Routine blood work review',
                        'Post-surgery follow-up', 'Chronic pain management',
                    ]),
                )
                symptoms = random.choice([
                    'Fever, headache, body ache', 'Chest pain, shortness of breath',
                    'Abdominal pain, nausea', 'Joint pain, swelling',
                    'Skin rash, itching', 'Fatigue, weight loss',
                    'Cough, sore throat', 'Dizziness, blurred vision',
                ])
                diagnosis = random.choice([
                    'Viral infection', 'Hypertension', 'Type 2 Diabetes',
                    'Migraine', 'Gastritis', 'Lower back pain',
                    'Upper respiratory infection', 'Allergic reaction',
                ])
                OPDVisit.objects.create(
                    patient=pat, doctor=doc, appointment=appt,
                    visit_date=appt.appointment_date,
                    symptoms=symptoms, diagnosis=diagnosis,
                    treatment='Prescribed medication and rest',
                    status=random.choice(['Waiting', 'In-Progress', 'Completed']),
                )
            if Appointment.objects.count() >= 100:
                break
        self.stdout.write('  Appointments & OPD created.')

        # 15. Medical Records
        for i, (user_p, pat) in enumerate(patients[:12]):
            doc_user, doc = doctors[i % len(doctors)]
            MedicalRecord.objects.create(
                patient=pat, doctor=doc_user,
                visit_date=today - timedelta(days=random.randint(1, 60)),
                diagnosis=random.choice([
                    'Hypertension Stage 1', 'Type 2 Diabetes Mellitus',
                    'Acute Bronchitis', 'Migraine with Aura',
                    'Osteoarthritis of Knee', 'GERD',
                    'Iron Deficiency Anemia', 'Urinary Tract Infection',
                ]),
                symptoms=random.choice([
                    'High blood pressure readings', 'Elevated blood sugar',
                    'Persistent cough', 'Recurring headaches',
                    'Joint stiffness', 'Acid reflux',
                ]),
                notes='Patient responded well to treatment. Follow up in 2 weeks.',
            )
        self.stdout.write('  Medical Records created.')

        # 16. Wards & Beds
        ward_types = [
            ('General Ward', 'General', 20, 'General Medicine', 500),
            ('ICU', 'ICU', 8, 'Cardiology', 2000),
            ('Private Ward', 'Private', 5, 'Surgery', 1500),
            ('Semi-Private Ward', 'Semi-Private', 10, 'General Medicine', 800),
            ('CCU', 'CCU', 6, 'Cardiology', 2500),
        ]
        wards = {}
        for name, wtype, cap, dept_name, rate in ward_types:
            w = Ward.objects.create(
                name=name, department=departments[dept_name],
                floor=random.choice([1, 2, 3]), capacity=cap, ward_type=wtype,
            )
            for j in range(1, cap + 1):
                Bed.objects.create(
                    ward=w, bed_number=f'{name[:3].upper()}-{j}',
                    bed_type='Normal' if wtype not in ['ICU', 'CCU'] else 'Ventilator',
                    daily_rate=Decimal(str(rate)),
                )
            wards[name] = w
        self.stdout.write('  Wards & Beds created.')

        # 17. Admissions
        for user_p, pat in patients[:5]:
            doc_user, doc = doctors[random.randint(0, 4)]
            ward = random.choice(list(wards.values()))
            bed = ward.beds.filter(status='Available').first()
            if bed:
                Admission.objects.create(
                    patient=pat, doctor=doc, ward=ward, bed=bed,
                    admission_type=random.choice(['Emergency', 'Elective', 'Referral']),
                    diagnosis=random.choice([
                        'Chest infection requiring IV antibiotics',
                        'Post-operative recovery',
                        'Cardiac monitoring',
                        'Severe dehydration',
                        'Pneumonia',
                    ]),
                    status='Admitted',
                )
        self.stdout.write('  Admissions created.')

        # 18. Medicine Categories & Medicines
        med_cats_data = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Ointment', 'Drops', 'Inhaler']
        categories = {}
        for name in med_cats_data:
            categories[name] = MedicineCategory.objects.create(name=name)

        suppliers_data = [
            ('Dawa Life Sciences', 'Muriuki', '+254711111111', 'sales@supplier.example.com'),
            ('Cosmos Ltd', 'Abdullahi', '+254722222222', 'sales@supplier.example.com'),
            ('Universal Corporation Ltd', 'Nzioka', '+254733333333', 'sales@supplier.example.com'),
            ('Regal Pharmaceuticals', 'Wanjala', '+254744444444', 'sales@supplier.example.com'),
            ('KEMSA', 'Omondi', '+254755555555', 'sales@supplier.example.com'),
        ]
        supplier_objs = []
        for name, cp, phone, email in suppliers_data:
            s = Supplier.objects.create(name=name, contact_person=cp, phone=phone, email=email)
            supplier_objs.append(s)

        med_data = [
            ('Panadol CF', 'Paracetamol+Phenylephrine', 'Tablet', 6.00, 250, 10, 'Dawa Life Sciences'),
            ('Panadol 500mg', 'Paracetamol', 'Tablet', 3.50, 500, 50, 'Dawa Life Sciences'),
            ('Panadol Extra', 'Paracetamol+ caffeine', 'Tablet', 5.00, 300, 30, 'Dawa Life Sciences'),
            ('Omeprazole 20mg', 'Omeprazole', 'Capsule', 8.00, 350, 40, 'Cosmos Ltd'),
            ('Omeprazole', 'Omeprazole', 'Capsule', 6.50, 200, 30, 'Cosmos Ltd'),
            ('Metformin 500mg', 'Metformin', 'Tablet', 4.00, 400, 50, 'Universal Corporation Ltd'),
            ('Metformin', 'Metformin', 'Tablet', 3.50, 350, 40, 'Universal Corporation Ltd'),
            ('Calcium + Vitamin D3', 'Calcium+Vitamin D3', 'Tablet', 12.00, 400, 30, 'Regal Pharmaceuticals'),
            ('Montelukast 10mg', 'Montelukast', 'Tablet', 15.00, 200, 25, 'Cosmos Ltd'),
            ('Fusidic Cream', 'Fusidic Acid', 'Ointment', 85.00, 120, 20, 'KEMSA'),
            ('Paracetamol 650mg', 'Paracetamol', 'Tablet', 4.50, 450, 50, 'Dawa Life Sciences'),
            ('Amoxicillin 500mg', 'Amoxicillin', 'Capsule', 10.00, 300, 40, 'Cosmos Ltd'),
            ('Cetirizine 10mg', 'Cetirizine', 'Tablet', 3.00, 400, 50, 'Universal Corporation Ltd'),
            ('Azithromycin 500mg', 'Azithromycin', 'Capsule', 18.00, 250, 30, 'Cosmos Ltd'),
            ('Salbutamol Inhaler', 'Salbutamol', 'Inhaler', 250.00, 80, 15, 'KEMSA'),
            ('Diclofenac Gel', 'Diclofenac', 'Ointment', 65.00, 150, 20, 'Regal Pharmaceuticals'),
            ('Pantoprazole 40mg', 'Pantoprazole', 'Tablet', 12.00, 280, 35, 'Universal Corporation Ltd'),
            ('Losartan 50mg', 'Losartan', 'Tablet', 8.50, 320, 40, 'Regal Pharmaceuticals'),
            ('Atorvastatin 20mg', 'Atorvastatin', 'Tablet', 15.00, 200, 25, 'Cosmos Ltd'),
            ('Insulin Glargine', 'Insulin', 'Injection', 350.00, 50, 10, 'KEMSA'),
        ]
        medicines = []
        for name, generic, cat, price, stock, min_stock, supplier_name in med_data:
            med = Medicine.objects.create(
                name=name, generic_name=generic, category_fk=categories[cat],
                category=cat, manufacturer=supplier_name.split()[0],
                unit_price=Decimal(str(price)), stock_quantity=stock,
                minimum_stock=min_stock,
                expiry_date=date(random.choice([2027, 2028]), random.randint(1, 12), random.randint(1, 28)),
                batch_number=f'BATCH-{random.randint(1000,9999)}',
            )
            supplier_obj = next((s for s in supplier_objs if s.name == supplier_name), supplier_objs[0])
            med.suppliers.add(supplier_obj)
            medicines.append(med)
        self.stdout.write('  Medicines created.')

        # 19. Prescriptions
        for i in range(50):
            user_p, pat = patients[i % len(patients)]
            doc_user, doc = doctors[i % len(doctors)]
            appt = Appointment.objects.filter(patient=pat).first()
            if appt:
                visit, _ = Visit.objects.get_or_create(
                    appointment=appt,
                    defaults={'doctor_notes': f'Dr. {doc} notes for {pat}'},
                )
                rx = Prescription.objects.create(
                    visit=visit, doctor=doc_user, patient=pat,
                    diagnosis=random.choice([
                        'Upper respiratory infection', 'Hypertension',
                        'Type 2 Diabetes', 'Migraine', 'Gastritis',
                    ]),
                    notes='Take medication as prescribed.',
                )
                for med in random.sample(medicines, min(random.randint(1, 4), len(medicines))):
                    PrescriptionItem.objects.create(
                        prescription=rx, medicine=med,
                        dosage=random.choice(['500mg', '250mg', '10mg', '20mg']),
                        frequency=random.choice(['Once Daily', 'Twice Daily', 'Three Times Daily']),
                        duration=random.choice(['5 days', '7 days', '10 days', '14 days']),
                        quantity=random.randint(10, 60),
                    )
        self.stdout.write('  Prescriptions created.')

        # 20. Lab Tests
        lab_tests = [
            ('Complete Blood Count', 500, '4.0-5.5 million/uL', 'million/uL'),
            ('Blood Sugar (Fasting)', 200, '70-100 mg/dL', 'mg/dL'),
            ('Lipid Profile', 800, 'Desirable < 200', 'mg/dL'),
            ('Thyroid Profile (TSH)', 1200, 'TSH 0.4-4.0 mIU/L', 'mIU/L'),
            ('Liver Function Test', 1000, 'AST 10-40 U/L', 'U/L'),
            ('Kidney Function Test', 900, 'Creatinine 0.6-1.2 mg/dL', 'mg/dL'),
            ('Urinalysis', 300, 'Normal', ''),
            ('HbA1c', 700, '< 5.7%', '%'),
            ('ECG', 500, 'Normal sinus rhythm', ''),
            ('C-Reactive Protein', 600, '< 10 mg/L', 'mg/L'),
        ]
        tests = []
        for name, price, norm, unit in lab_tests:
            tests.append(LabTest.objects.create(
                name=name, price=Decimal(str(price)),
                normal_range=norm, unit=unit,
                department=departments['Pathology'],
            ))
        self.stdout.write('  Lab Tests created.')

        # 21. Lab Orders & Results
        for i in range(50):
            user_p, pat = patients[i % len(patients)]
            doc_user, doc = doctors[i % len(doctors)]
            order_status = random.choice(['Pending', 'In-Progress', 'Completed', 'Completed'])
            order = LabOrder.objects.create(
                patient=pat, doctor=doc_user,
                status=order_status,
                priority=random.choice(['Routine', 'Routine', 'Urgent', 'STAT']),
            )
            for test in random.sample(tests, min(random.randint(2, 4), len(tests))):
                item = LabOrderItem.objects.create(order=order, test=test)
                if order_status == 'Completed':
                    abnormal = random.random() > 0.7
                    LabResult.objects.create(
                        order_item=item,
                        result_value=f'{random.uniform(3.5, 6.0):.1f}',
                        reference_range=test.normal_range,
                        is_abnormal=abnormal,
                        uploaded_by=random.choice(lab_tech_users),
                    )
        self.stdout.write('  Lab Orders & Results created.')

        # 22. Radiology Tests
        rad_tests = [
            ('X-Ray Chest', 1500, 'Chest imaging'),
            ('CT Scan Head', 5000, 'Brain computed tomography'),
            ('MRI Brain', 8000, 'Brain magnetic resonance imaging'),
            ('Ultrasound Abdomen', 2500, 'Abdominal ultrasound'),
            ('X-Ray Knee', 1200, 'Knee joint imaging'),
            ('CT Scan Spine', 6000, 'Spine computed tomography'),
            ('Mammography', 3000, 'Breast imaging'),
            ('DEXA Scan', 4000, 'Bone density scan'),
        ]
        rad_test_objs = []
        for name, price, desc in rad_tests:
            rad_test_objs.append(RadiologyTest.objects.create(
                name=name, price=Decimal(str(price)), description=desc,
            ))
        self.stdout.write('  Radiology Tests created.')

        # 23. Radiology Orders
        for i, (user_p, pat) in enumerate(patients[:8]):
            doc_user, doc = doctors[i % len(doctors)]
            test = random.choice(rad_test_objs)
            order_status = random.choice(['Pending', 'In-Progress', 'Completed', 'Completed'])
            rad_order = RadiologyOrder.objects.create(
                patient=pat, doctor=doc_user, test=test,
                clinical_information=random.choice([
                    'Persistent headache for 2 weeks',
                    'Chest pain evaluation',
                    'Abdominal pain investigation',
                    'Follow-up imaging',
                    'Pre-surgical assessment',
                ]),
                status=order_status,
                priority=random.choice(['Routine', 'Urgent']),
            )
            if order_status == 'Completed':
                RadiologyReport.objects.create(
                    order=rad_order,
                    findings=random.choice([
                        'No abnormality detected.',
                        'Mild cardiomegaly noted.',
                        'Bilateral lower lobe infiltrates.',
                        'Degenerative changes in lumbar spine.',
                        'Normal brain parenchyma.',
                    ]),
                    impression=random.choice([
                        'Normal study.',
                        'Mild findings, correlate clinically.',
                        'Recommend follow-up in 3 months.',
                        'No acute abnormality.',
                    ]),
                    reported_by=random.choice(lab_tech_users),
                )
        self.stdout.write('  Radiology Orders created.')

        # 24. Insurance Patient Links (ensuring good coverage)
        for i, (user_p, pat) in enumerate(patients[:15]):
            if not PatientInsurance.objects.filter(patient=pat).exists() and pat.insurance_provider:
                PatientInsurance.objects.create(
                    patient=pat, plan=pat.insurance_provider,
                    policy_number=f'POL-2026-{str(i+100).zfill(4)}',
                    start_date=today - timedelta(days=random.randint(10, 90)),
                    end_date=today + timedelta(days=random.randint(180, 365)),
                )
        self.stdout.write('  Patient Insurance records ensured.')

        # 25. Invoices & Payments
        for i in range(50):
            user_p, pat = patients[i % len(patients)]
            inv = Invoice.objects.create(
                patient=pat, total_amount=Decimal(str(random.randint(2000, 25000))),
                status=random.choice(['Pending', 'Partial', 'Paid', 'Paid']),
                created_by=acc_user,
            )
            items_data = [
                ('Consultation Fee', 1, random.choice([1000, 1500, 2000])),
                ('Lab Tests', random.randint(1, 3), 500),
                ('Pharmacy', random.randint(1, 5), random.choice([100, 200, 350])),
                ('Radiology', 1, random.choice([1500, 2500, 5000])),
            ]
            for desc, qty, price in random.sample(items_data, random.randint(1, 3)):
                InvoiceItem.objects.create(
                    invoice=inv, description=desc,
                    quantity=qty, unit_price=Decimal(str(price)),
                )
            if inv.status in ['Paid', 'Partial']:
                paid = inv.net_amount if inv.status == 'Paid' else inv.net_amount * Decimal('0.5')
                Payment.objects.create(
                    invoice=inv, amount=paid,
                    **ke.payment(),
                    received_by=acc_user,
                )
        self.stdout.write('  Invoices & Payments created.')

        # 26. Nursing Stations & Tasks
        for ward_name, ward in wards.items():
            nurse = random.choice(nurse_users)
            NursingStation.objects.create(
                name=f'Station {ward_name}',
                ward=ward, capacity=ward.capacity,
                nurse_in_charge=nurse,
            )
        for i, (user_p, pat) in enumerate(patients[:8]):
            nurse = random.choice(nurse_users)
            NursingTask.objects.create(
                patient=pat, assigned_to=nurse,
                task_type=random.choice(['Medication', 'Vitals', 'Wound Care', 'IV']),
                description=random.choice([
                    'Administer morning medication',
                    'Record vital signs',
                    'Change wound dressing',
                    'IV line check',
                    'Pre-operative preparation',
                ]),
                scheduled_time=timezone.now() + timedelta(hours=random.randint(1, 24)),
                status=random.choice(['Pending', 'In-Progress', 'Completed']),
            )
        self.stdout.write('  Nursing Stations & Tasks created.')

        # 27. Vital Signs
        for i, (user_p, pat) in enumerate(patients[:10]):
            VitalSigns.objects.create(
                patient=pat, recorded_by=random.choice(nurse_users),
                temperature=Decimal(str(round(random.uniform(36.0, 38.5), 1))),
                blood_pressure_systolic=random.randint(100, 160),
                blood_pressure_diastolic=random.randint(60, 100),
                heart_rate=random.randint(55, 110),
                respiratory_rate=random.randint(12, 22),
                oxygen_saturation=Decimal(str(round(random.uniform(93.0, 99.0), 1))),
                weight=Decimal(str(round(random.uniform(40.0, 95.0), 2))),
            )
        self.stdout.write('  Vital Signs created.')

        # 28. Ambulance
        ambulances = [
            ('KDJ 101A', 'AC', 'Muli Driver', '+254720000000', 'Hospital'),
            ('KDK 202B', 'ICU', 'Juma Driver', '+254730000000', 'En route'),
            ('KDL 303C', 'Basic', 'Wekesa Driver', '+254740000000', 'Hospital'),
            ('KDM 404D', 'AC', 'Gitonga Driver', '+254750000000', 'On Call'),
        ]
        amb_objs = []
        for vnum, vtype, dname, dphone, loc in ambulances:
            amb_objs.append(Ambulance.objects.create(
                vehicle_number=vnum, vehicle_type=vtype,
                driver_name=dname, driver_phone=dphone, current_location=loc,
            ))
        amb_requests = [
            ('Emergency Patient 1', '+254740000001', 'Westlands', 'Medcare Hospital', 'Completed'),
            ('Emergency Patient 2', '+254740000002', 'Kilimani', 'Medcare Hospital', 'In-Transit'),
            ('Transfer Patient', '+254740000003', 'Medcare Hospital', 'Kenyatta National Hospital', 'Dispatched'),
            ('Emergency Patient 3', '+254740000004', 'Lavington', 'Medcare Hospital', 'Pending'),
        ]
        for pname, pphone, pickup, dropoff, status in amb_requests:
            AmbulanceRequest.objects.create(
                patient_name=pname, patient_phone=pphone,
                pickup_location=pickup, dropoff_location=dropoff,
                ambulance=random.choice(amb_objs), status=status,
                requested_by=admin,
                distance_km=Decimal(str(round(random.uniform(2.0, 15.0), 2))),
            )
        self.stdout.write('  Ambulance created.')

        # 29. Inventory
        inv_cats_data = [
            ('Medical Supplies', 'Consumable', [
                ('Surgical Gloves', 'Box', 250, 50, 200, 'Store Room A'),
                ('Face Masks', 'Box', 150, 100, 150, 'Store Room A'),
                ('Syringes (5ml)', 'Piece', 5, 2000, 1000, 'Store Room B'),
                ('Bandages', 'Roll', 30, 500, 200, 'Store Room B'),
                ('IV Cannula', 'Piece', 25, 800, 300, 'Store Room A'),
                ('Cotton Swabs', 'Packet', 40, 600, 250, 'Store Room B'),
            ]),
            ('Equipment', 'Equipment', [
                ('Stethoscope', 'Piece', 1500, 20, 10, 'Equipment Room'),
                ('Blood Pressure Monitor', 'Piece', 2500, 15, 5, 'Equipment Room'),
                ('Pulse Oximeter', 'Piece', 1800, 25, 8, 'Equipment Room'),
                ('Thermometer (Digital)', 'Piece', 500, 30, 10, 'Equipment Room'),
                ('Defibrillator', 'Piece', 45000, 3, 1, 'Emergency'),
            ]),
            ('Surgical Instruments', 'Supplies', [
                ('Surgical Scissors', 'Piece', 800, 30, 10, 'OT Store'),
                ('Forceps', 'Piece', 600, 25, 8, 'OT Store'),
                ('Scalpel', 'Piece', 200, 100, 30, 'OT Store'),
            ]),
        ]
        for cat_name, item_type, items in inv_cats_data:
            cat = InventoryCategory.objects.create(name=cat_name)
            for iname, unit, price, qty, reorder, loc in items:
                InventoryItem.objects.create(
                    name=iname, category=cat, item_type=item_type,
                    quantity=qty, unit=unit, unit_price=Decimal(str(price)),
                    reorder_level=reorder, location=loc,
                )
        self.stdout.write('  Inventory created.')

        # 30. Purchase Orders
        inv_items = InventoryItem.objects.all()
        for item in random.sample(list(inv_items), min(5, inv_items.count())):
            PurchaseOrder.objects.create(
                item=item,
                supplier_name=random.choice(supplier_objs).name,
                quantity=random.randint(50, 500),
                total_cost=Decimal(str(random.randint(5000, 50000))),
                order_date=today - timedelta(days=random.randint(1, 15)),
                expected_delivery=today + timedelta(days=random.randint(3, 14)),
                status=random.choice(['Pending', 'Ordered', 'Delivered']),
                ordered_by=acc_user,
            )
        self.stdout.write('  Purchase Orders created.')

        # 31. HR Designations
        for dept_name in ['Cardiology', 'Neurology', 'Surgery', 'Orthopedics', 'General Medicine']:
            Designation.objects.create(
                name=f'{dept_name} Head', department=departments[dept_name],
            )
        Designation.objects.create(name='Floor Nurse', department=departments['General Medicine'])
        Designation.objects.create(name='Senior Pharmacist', department=departments['Pharmacy'])
        self.stdout.write('  HR Designations created.')

        # 32. HR Records
        all_employees = Employee.objects.all()
        for emp in random.sample(list(all_employees), min(8, all_employees.count())):
            HRRecord.objects.create(
                employee=emp,
                record_type=random.choice(['Appointment', 'Promotion', 'Increment']),
                effective_date=today - timedelta(days=random.randint(30, 365)),
                description=random.choice([
                    f'{emp.user.get_full_name()} promoted to senior position',
                    f'Annual increment for {emp.user.get_full_name()}',
                    f'New appointment - {emp.designation}',
                ]),
                created_by=hr_user,
            )
        self.stdout.write('  HR Records created.')

        # 33. Training
        trainings = [
            ('Patient Safety Training', 'Annual patient safety refresher', 'Dr. Abdi Abdullahi', 'Completed'),
            ('CPR & First Aid', 'Basic life support training', 'Dr. Kerubo Kariuki', 'Completed'),
            ('Infection Control', 'Hospital infection prevention protocols', 'Dr. Mwangi Omondi', 'Ongoing'),
            ('New Staff Orientation', 'Orientation for new employees', 'HR Team', 'Planned'),
            ('Emergency Response Drill', 'Fire and emergency evacuation drill', 'Safety Officer', 'Planned'),
        ]
        for title, desc, trainer, status in trainings:
            Training.objects.create(
                title=title, description=desc, trainer=trainer,
                start_date=today + timedelta(days=random.randint(-30, 30)),
                end_date=today + timedelta(days=random.randint(-25, 35)),
                status=status,
            )
        self.stdout.write('  Training created.')

        # 34. Attendance
        for emp in random.sample(list(all_employees), min(15, all_employees.count())):
            for d in range(5):
                att_date = today - timedelta(days=d)
                Attendance.objects.create(
                    employee=emp, date=att_date,
                    check_in=time(random.randint(8, 10), random.choice([0, 15, 30])),
                    check_out=time(random.randint(16, 18), random.choice([0, 30])),
                    status=random.choice(['Present', 'Present', 'Present', 'Late']),
                )
        self.stdout.write('  Attendance created.')

        # 35. Leave Requests
        for emp in random.sample(list(all_employees), min(6, all_employees.count())):
            LeaveRequest.objects.create(
                employee=emp,
                leave_type=random.choice(['Sick', 'Casual', 'Earned']),
                start_date=today + timedelta(days=random.randint(1, 30)),
                end_date=today + timedelta(days=random.randint(2, 35)),
                reason=random.choice([
                    'Personal reasons', 'Medical appointment',
                    'Family event', 'Annual leave',
                ]),
                status=random.choice(['Pending', 'Approved', 'Rejected']),
                approved_by=hr_user,
            )
        self.stdout.write('  Leave Requests created.')

        # 36. Notifications
        notif_data = [
            ('Appointment Reminder', 'You have an upcoming appointment tomorrow.', 'Appointment'),
            ('Lab Results Ready', 'Your lab test results are now available.', 'Laboratory'),
            ('Invoice Generated', 'A new invoice has been generated for your visit.', 'Billing'),
            ('Prescription Ready', 'Your prescription is ready for pickup.', 'Pharmacy'),
            ('Insurance Claim Update', 'Your insurance claim has been processed.', 'General'),
            ('Low Stock Alert', 'Medicine stock is running low, please reorder.', 'Alert'),
            ('Payment Received', 'Payment of KSh 5,000 has been received.', 'Billing'),
            ('Appointment Confirmed', 'Your appointment with Dr. Abdullahi has been confirmed.', 'Appointment'),
        ]
        for user_p, pat in patients[:10]:
            title, msg, ntype = random.choice(notif_data)
            Notification.objects.create(
                recipient=user_p, sender=admin,
                title=title, message=msg, notification_type=ntype,
                is_read=random.choice([True, False]),
            )
        self.stdout.write('  Notifications created.')

        # 37. Audit Logs
        for staff_user in random.sample(all_staff, min(10, len(all_staff))):
            for action in ['Create', 'Update', 'View']:
                AuditLog.objects.create(
                    user=staff_user, action=action,
                    model_name=random.choice(['Patient', 'Appointment', 'Invoice', 'Medicine']),
                    object_id=str(random.randint(1, 20)),
                    description=f'{action} action by {staff_user.get_full_name()}',
                    ip_address='127.0.0.1',
                    path=f'/{random.choice(["patients", "appointments", "billing", "pharmacy"])}/',
                    method='GET',
                )
        self.stdout.write('  Audit Logs created.')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== SEED DATA SUMMARY ==='))
        self.stdout.write(self.style.SUCCESS(f'  Users:          {User.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Employees:      {Employee.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Doctors:        {Doctor.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Patients:       {Patient.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Appointments:   {Appointment.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  OPD Visits:     {OPDVisit.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Admissions:     {Admission.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Medicines:      {Medicine.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Lab Orders:     {LabOrder.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Radiology:      {RadiologyOrder.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Invoices:       {Invoice.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Insurance:      {PatientInsurance.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Inventory:      {InventoryItem.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Notifications:  {Notification.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  Audit Logs:     {AuditLog.objects.count()}'))
