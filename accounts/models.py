from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Hospital Administrator'
        DOCTOR = 'DOCTOR', 'Doctor'
        RECEPTIONIST = 'RECEPTIONIST', 'Receptionist'
        PATIENT = 'PATIENT', 'Patient'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
        help_text="Designated user role within MediQueue"
    )
    phone_number = models.CharField(max_length=20, blank=True, help_text="Contact telephone number")
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_doctor_role(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_receptionist_role(self):
        return self.role == self.Role.RECEPTIONIST

    @property
    def is_patient_role(self):
        return self.role == self.Role.PATIENT

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            if self.is_doctor_role and not self.first_name.startswith('Dr'):
                return f"Dr. {self.first_name} {self.last_name}"
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"
