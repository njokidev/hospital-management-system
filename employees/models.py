from django.db import models
from django.conf import settings
from departments.models import Department
from core.kenya import REGULATORY_BODY_CHOICES, validate_kra_pin, validate_national_id


class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    designation = models.CharField(max_length=200)
    date_of_joining = models.DateField()
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    # ── Kenyan statutory & payroll identifiers ──
    national_id = models.CharField('National ID', max_length=12, blank=True, validators=[validate_national_id])
    kra_pin = models.CharField('KRA PIN', max_length=11, blank=True, validators=[validate_kra_pin])
    nssf_number = models.CharField('NSSF number', max_length=20, blank=True)
    sha_number = models.CharField('SHA member number', max_length=30, blank=True)

    # ── Professional registration (KMPDC, NCK, PPB, COC, KMLTTB …) ──
    regulatory_body = models.CharField(max_length=10, choices=REGULATORY_BODY_CHOICES, blank=True)
    license_number = models.CharField('Registration / licence number', max_length=50, blank=True)
    license_expiry = models.DateField('Practising licence expiry', null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self._normalise_identifiers()
        if not self.employee_id:
            last = Employee.objects.all().order_by('-id').first()
            if last:
                last_num = int(last.employee_id.split('-')[1])
                self.employee_id = f'EMP-{str(last_num + 1).zfill(5)}'
            else:
                self.employee_id = 'EMP-00001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    def _normalise_identifiers(self):
        if self.kra_pin:
            self.kra_pin = self.kra_pin.strip().upper()

    @property
    def license_status(self):
        """'expired', 'expiring' (≤30 days), 'valid' or '' when not tracked."""
        if not self.license_expiry:
            return ''
        from django.utils import timezone
        days = (self.license_expiry - timezone.localdate()).days
        if days < 0:
            return 'expired'
        if days <= 30:
            return 'expiring'
        return 'valid'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(blank=True, null=True)
    check_out = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-date']
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"


class LeaveRequest(models.Model):
    # Aligned with the Employment Act, 2007 (Kenya)
    LEAVE_TYPE_CHOICES = [
        ('Annual', 'Annual (21 working days/yr)'),
        ('Sick', 'Sick'),
        ('Maternity', 'Maternity (3 months)'),
        ('Paternity', 'Paternity (2 weeks)'),
        ('Compassionate', 'Compassionate'),
        ('Study', 'Study'),
        ('Unpaid', 'Unpaid'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"
