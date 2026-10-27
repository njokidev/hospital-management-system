from django.db import models
from django.conf import settings


class MedicineCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Medicine Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Syrup', 'Syrup'),
        ('Injection', 'Injection'),
        ('Ointment', 'Ointment'),
        ('Drops', 'Drops'),
        ('Inhaler', 'Inhaler'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    category_fk = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='medicines')
    manufacturer = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=10)
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=100, blank=True)
    suppliers = models.ManyToManyField(Supplier, blank=True, related_name='medicines')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.generic_name})"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    @property
    def is_expiring_soon(self):
        from datetime import timedelta
        from django.utils import timezone
        return self.expiry_date <= timezone.now().date() + timedelta(days=90)


class Prescription(models.Model):
    visit = models.OneToOneField('appointments.Visit', on_delete=models.CASCADE, related_name='prescription')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    is_dispensed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription {self.prescription_number} for {self.patient} by Dr. {self.doctor}"

    @property
    def prescription_number(self):
        return f"RX-{str(self.pk).zfill(6)}"

    @property
    def dispensed_by(self):
        try:
            return self.dispensation.dispensed_by
        except DispensedMedicine.DoesNotExist:
            return None

    @property
    def dispensed_at(self):
        try:
            return self.dispensation.dispensed_at
        except DispensedMedicine.DoesNotExist:
            return None

    @property
    def dispensed_status(self):
        return "Dispensed" if self.is_dispensed else "Pending"


class PrescriptionItem(models.Model):
    FREQUENCY_CHOICES = [
        ('Once Daily', 'Once Daily'),
        ('Twice Daily', 'Twice Daily'),
        ('Three Times Daily', 'Three Times Daily'),
        ('Four Times Daily', 'Four Times Daily'),
        ('Every 4 Hours', 'Every 4 Hours'),
        ('Every 6 Hours', 'Every 6 Hours'),
        ('Every 8 Hours', 'Every 8 Hours'),
        ('As Needed', 'As Needed'),
        ('Before Bed', 'Before Bed'),
        ('Morning', 'Morning'),
    ]

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES)
    duration = models.CharField(max_length=100)
    quantity = models.IntegerField()
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.dosage} {self.frequency}"


class DispensedMedicine(models.Model):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE, related_name='dispensation')
    dispensed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dispensed_at = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = 'Dispensed Medicines'

    def __str__(self):
        return f"Dispensed: {self.prescription} - {settings.CURRENCY_SYMBOL} {self.total_cost}"
