from django.db import models
from doctors.models import Department, DoctorProfile


class HospitalResource(models.Model):
    class ResourceType(models.TextChoices):
        CONSULTATION_ROOM = 'ROOM', 'Consultation Room'
        ICU_BED = 'ICU', 'ICU Bed'
        EMERGENCY_BAY = 'EMERGENCY', 'Emergency Bay'
        DIAGNOSTIC_ROOM = 'DIAGNOSTIC', 'Diagnostic Lab / Room'
        GENERAL_BED = 'BED', 'General Ward Bed'

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        RESERVED = 'RESERVED', 'Reserved'

    name = models.CharField(max_length=100, help_text="e.g., Cardiology Suite 101, Ultrasound Room B")
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.CONSULTATION_ROOM
    )
    room_number = models.CharField(max_length=20, unique=True, help_text="Room / Bay identifier e.g. R-101")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resources'
    )
    assigned_doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='allocated_resources',
        help_text="Doctor currently occupying or assigned to this room"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    capacity = models.PositiveIntegerField(default=1, help_text="Patient handling capacity")
    notes = models.TextField(blank=True, help_text="Equipment present or maintenance notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"{self.room_number} - {self.name} [{self.get_status_display()}]"
