from django import forms
from .models import QueueToken, Consultation
from doctors.models import Department, DoctorProfile
from accounts.models import CustomUser


class WalkInTokenForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_department_token'}),
        empty_label="-- Select Department --"
    )
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.filter(is_available=True).select_related('user', 'department'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor_token'}),
        empty_label="-- Select Doctor --"
    )
    patient = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=CustomUser.Role.PATIENT).select_related('patient_profile'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_patient_token'}),
        empty_label="-- Select Registered Patient --"
    )

    class Meta:
        model = QueueToken
        fields = ['patient', 'department', 'doctor', 'priority', 'priority_notes']
        widgets = {
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'priority_notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mandatory clinical reason if Emergency'}),
        }


class EmergencyPriorityForm(forms.Form):
    reason = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter medical reason (e.g., Chest pain, severe trauma, acute respiratory distress)'
        })
    )


class ConsultationForm(forms.ModelForm):
    bp = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 120/80 mmHg'})
    )
    pulse = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 74 bpm'})
    )
    temperature = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 98.6 °F'})
    )
    spo2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 99%'})
    )

    class Meta:
        model = Consultation
        fields = ['symptoms', 'diagnosis', 'prescription', 'follow_up_date', 'notes']
        widgets = {
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Presenting symptoms / history...'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Clinical diagnosis...'}),
            'prescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Medication name, dosage, frequency, and instructions...'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal clinical notes, lab tests ordered, precautions...'}),
        }
