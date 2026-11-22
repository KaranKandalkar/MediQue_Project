from django.db import models
from django.conf import settings
from django.utils import timezone
from doctors.models import Department, DoctorProfile


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_date = models.DateField(help_text="Scheduled visit date")
    appointment_time = models.TimeField(help_text="Scheduled slot time")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    reason = models.TextField(help_text="Chief complaint / Reason for visit")
    notes = models.TextField(blank=True, help_text="Staff or doctor preparation notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                name='unique_doctor_date_time_slot'
            )
        ]

    def __str__(self):
        return f"{self.patient.display_name} with {self.doctor.full_name} on {self.appointment_date} at {self.appointment_time.strftime('%H:%M')}"

    @property
    def is_cancellable(self):
        """Patients can cancel pending scheduled appointments before or on appointment day."""
        if self.status != self.Status.SCHEDULED:
            return False
        return self.appointment_date >= timezone.localdate()
