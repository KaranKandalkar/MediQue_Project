from django import forms
from .models import HospitalResource


class HospitalResourceForm(forms.ModelForm):
    class Meta:
        model = HospitalResource
        fields = ['name', 'resource_type', 'room_number', 'department', 'assigned_doctor', 'status', 'capacity', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Room 101 - Cardiology Consultation'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. R-101'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'assigned_doctor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Equipment, notes...'}),
        }
