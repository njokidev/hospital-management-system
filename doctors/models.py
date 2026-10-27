from django.db import models
from django.conf import settings
from employees.models import Employee
from departments.models import Specialization


class Doctor(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    years_of_experience = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        ordering = ['-created_at']

    def __str__(self):
        return f"Dr. {self.employee.user.get_full_name()} - {self.specialization}" if self.specialization else f"Dr. {self.employee.user.get_full_name()}"

    @property
    def user(self):
        return self.employee.user

    @property
    def full_name(self):
        return self.employee.user.get_full_name() or self.employee.user.username

    @property
    def department(self):
        return self.employee.department

    @property
    def kmpdc_number(self):
        """KMPDC registration number (stored on the linked Employee)."""
        return self.employee.license_number


class DoctorSchedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Doctor Schedule'
        verbose_name_plural = 'Doctor Schedules'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.day_of_week} ({self.start_time} to {self.end_time})"


class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.PositiveIntegerField(default=20)
    current_patients = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Doctor Availability'
        verbose_name_plural = 'Doctor Availabilities'
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time} to {self.end_time})"

    @property
    def slots_remaining(self):
        return self.max_patients - self.current_patients

    @property
    def is_fully_booked(self):
        return self.current_patients >= self.max_patients
