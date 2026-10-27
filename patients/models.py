from django.db import models
from django.conf import settings

from core.kenya import COUNTY_CHOICES, ID_TYPE_CHOICES, RELATIONSHIP_CHOICES


class Patient(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)

    # ── Kenyan identification & residence ──
    id_type = models.CharField('ID type', max_length=20, choices=ID_TYPE_CHOICES, default='national_id')
    id_number = models.CharField('ID / document number', max_length=30, blank=True, db_index=True)
    sha_number = models.CharField(
        'SHA member number', max_length=30, blank=True, db_index=True,
        help_text='Social Health Authority (SHIF) membership number',
    )
    county = models.CharField(max_length=30, choices=COUNTY_CHOICES, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)
    ward = models.CharField('Ward / estate', max_length=100, blank=True)
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(
        'Next of kin relationship', max_length=20, choices=RELATIONSHIP_CHOICES, blank=True,
    )
    insurance_provider = models.ForeignKey(
        'insurance.InsurancePlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last = Patient.objects.all().order_by('-id').first()
            if last:
                last_num = int(last.patient_id.split('-')[1])
                self.patient_id = f'PAT-{str(last_num + 1).zfill(5)}'
            else:
                self.patient_id = 'PAT-00001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    def get_full_name(self):
        return self.user.get_full_name()

    def get_short_name(self):
        return self.user.get_short_name()


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='medical_records')
    visit_date = models.DateField()
    diagnosis = models.TextField()
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.patient} - {self.visit_date} - {self.diagnosis[:50]}"


class PatientDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('id_proof', 'ID Proof'),
        ('insurance_card', 'Insurance Card'),
        ('lab_report', 'Lab Report'),
        ('prescription', 'Prescription'),
        ('discharge_summary', 'Discharge Summary'),
        ('other', 'Other'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='other')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='patient_documents/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Patient Document'
        verbose_name_plural = 'Patient Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.patient} - {self.title}"
