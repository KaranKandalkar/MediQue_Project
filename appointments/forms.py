from django import forms
from django.utils import timezone
from .models import Appointment
from doctors.models import Department, DoctorProfile
from accounts.models import CustomUser


class AppointmentBookingForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department_select'}),
        empty_label="-- Select Department --"
    )
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(is_available=True).select_related('user', 'department'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor_select'}),
        empty_label="-- Select Doctor --"
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.localdate().isoformat()
        })
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'step': '900'  # 15 minute increments
        })
    )

    class Meta:
        model = Appointment
        fields = ['department', 'doctor', 'appointment_date', 'appointment_time', 'reason', 'notes']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe your symptoms or reason for visit...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes for staff'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        app_date = cleaned_data.get('appointment_date')
        app_time = cleaned_data.get('appointment_time')

        if doctor and app_date and app_time:
            # 1. Check if date is in the past
            if app_date < timezone.localdate():
                self.add_error('appointment_date', "Cannot schedule appointments for past dates.")

            # 2. Check duplicate/conflicting slot for this doctor
            conflicting = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=app_date,
                appointment_time=app_time,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CHECKED_IN]
            )
            if self.instance and self.instance.pk:
                conflicting = conflicting.exclude(pk=self.instance.pk)

            if conflicting.exists():
                self.add_error('appointment_time', f"Dr. {doctor.full_name} already has an appointment booked at {app_time.strftime('%H:%M')} on this date. Please choose another time slot.")

            # 3. Check daily capacity of the doctor
            day_bookings_count = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=app_date,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CHECKED_IN, Appointment.Status.COMPLETED]
            ).count()

            if day_bookings_count >= doctor.daily_capacity:
                self.add_error('appointment_date', f"Dr. {doctor.full_name} has reached the maximum appointment capacity ({doctor.daily_capacity}) for this date.")

        return cleaned_data
