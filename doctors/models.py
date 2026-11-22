from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short uppercase department code for tokens, e.g., CARD, PEDI, ORTH"
    )
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-hospital', help_text="Bootstrap icon name, e.g. bi-heart-pulse")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def active_doctors_count(self):
        return self.doctors.filter(is_available=True).count()


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctors'
    )
    specialization = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150, help_text="e.g. MBBS, MD (Cardiology), FRCP")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    room_number = models.CharField(max_length=50, blank=True, help_text="Consultation room / cabin number")
    avg_consultation_time = models.PositiveIntegerField(
        default=15,
        help_text="Average consultation duration per patient in minutes"
    )
    daily_capacity = models.PositiveIntegerField(
        default=30,
        help_text="Maximum number of appointments/tokens handled per day"
    )
    is_available = models.BooleanField(default=True, help_text="Current duty/active availability status")
    available_days = models.CharField(
        max_length=100,
        default='Monday,Tuesday,Wednesday,Thursday,Friday',
        help_text="Comma-separated available days"
    )
    shift_start = models.TimeField(default='09:00:00')
    shift_end = models.TimeField(default='17:00:00')

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        dept_str = f" - {self.department.name}" if self.department else ""
        return f"{self.user.display_name}{dept_str}"

    @property
    def full_name(self):
        return self.user.display_name
