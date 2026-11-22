import random
import string
from django.db import models
from django.conf import settings
from django.utils import timezone


class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

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

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Hospital Patient Unique ID (e.g. PAT-2026-0001)"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True, help_text="Emergency phone number")
    address = models.TextField(blank=True)
    medical_history = models.TextField(blank=True, help_text="Past conditions, chronic illnesses, surgeries")
    allergies = models.TextField(blank=True, help_text="Known drug, food, or chemical allergies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.patient_id:
            year = timezone.now().year
            rand_code = ''.join(random.choices(string.digits, k=5))
            self.patient_id = f"PAT-{year}-{rand_code}"
            # Ensure uniqueness
            while PatientProfile.objects.filter(patient_id=self.patient_id).exists():
                rand_code = ''.join(random.choices(string.digits, k=5))
                self.patient_id = f"PAT-{year}-{rand_code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.display_name} ({self.patient_id})"

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.localdate()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
