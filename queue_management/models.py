from django.db import models
from django.conf import settings
from django.utils import timezone
from doctors.models import Department, DoctorProfile
from appointments.models import Appointment


class QueueToken(models.Model):
    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        EMERGENCY = 'EMERGENCY', 'Emergency Priority'

    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        CALLED = 'CALLED', 'Called to Room'
        IN_CONSULTATION = 'IN_CONSULTATION', 'In Consultation'
        COMPLETED = 'COMPLETED', 'Completed'
        SKIPPED = 'SKIPPED', 'Skipped'
        CANCELLED = 'CANCELLED', 'Cancelled'

    token_number = models.CharField(
        max_length=30,
        help_text="Formatted display token, e.g. CARD-001 or GEN-015"
    )
    token_sequence = models.PositiveIntegerField(
        help_text="Sequential integer token for the doctor on token_date"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_tokens'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='queue_tokens'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='queue_tokens'
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tokens',
        help_text="Linked appointment if booked in advance"
    )
    token_date = models.DateField(default=timezone.localdate)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    priority_assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_tokens_assigned',
        help_text="Authorized staff member who assigned emergency priority"
    )
    priority_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Clinical justification for emergency bump"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )
    estimated_wait_time = models.PositiveIntegerField(
        default=0,
        help_text="Calculated estimated wait time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    consultation_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['priority', 'token_sequence']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'token_date', 'token_sequence'],
                name='unique_doctor_daily_token_sequence'
            )
        ]

    def __str__(self):
        return f"{self.token_number} - {self.patient.display_name} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in [self.Status.WAITING, self.Status.CALLED, self.Status.IN_CONSULTATION]

    @property
    def is_emergency(self):
        return self.priority == self.Priority.EMERGENCY

    def calculate_position_and_wait_time(self):
        """
        Calculates the 1-based position of this token in the active waiting queue for its doctor today,
        and estimates the remaining wait time in minutes.
        Emergency patients are prioritized ahead of normal patients.
        """
        if self.status != self.Status.WAITING:
            return 0, 0

        # All waiting tokens for this doctor today
        waiting_tokens = QueueToken.objects.filter(
            doctor=self.doctor,
            token_date=self.token_date,
            status=self.Status.WAITING
        ).order_by('priority', 'token_sequence')

        # Find how many are ahead
        ahead_count = 0
        for tok in waiting_tokens:
            if tok.id == self.id:
                break
            ahead_count += 1

        # Check if a consultation is currently ongoing for this doctor
        in_consult = QueueToken.objects.filter(
            doctor=self.doctor,
            token_date=self.token_date,
            status__in=[self.Status.IN_CONSULTATION, self.Status.CALLED]
        ).first()

        avg_time = self.doctor.avg_consultation_time or 15
        base_wait = ahead_count * avg_time
        if in_consult:
            # Add estimated remaining time for current patient (half avg time minimum)
            base_wait += max(5, avg_time // 2)

        return ahead_count + 1, base_wait


class Consultation(models.Model):
    token = models.OneToOneField(
        QueueToken,
        on_delete=models.CASCADE,
        related_name='consultation'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='consultations'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations'
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    symptoms = models.TextField(blank=True, help_text="Chief complaints reported by patient")
    diagnosis = models.TextField(help_text="Clinical diagnosis")
    prescription = models.TextField(help_text="Prescribed medications, dosage, and intake instructions")
    vital_signs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Vitals e.g. blood_pressure, pulse, temp, spo2"
    )
    follow_up_date = models.DateField(null=True, blank=True, help_text="Recommended follow-up visit date")
    notes = models.TextField(blank=True, help_text="Doctor internal clinical advice or lab orders")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Consultation: {self.token.token_number} - {self.patient.display_name} with {self.doctor.full_name}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('QUEUE', 'Queue Update'),
        ('APPOINTMENT', 'Appointment Alert'),
        ('EMERGENCY', 'Emergency Notification'),
        ('SYSTEM', 'System Message'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='QUEUE')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.user.username}: {self.title}"
