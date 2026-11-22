from django import forms
from .models import DoctorProfile, Department
from accounts.models import CustomUser


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Cardiology'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CARD'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Department description'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-heart-pulse'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DoctorProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Email'})
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )

    class Meta:
        model = DoctorProfile
        fields = [
            'department', 'specialization', 'qualification', 'consultation_fee',
            'room_number', 'avg_consultation_time', 'daily_capacity', 'is_available',
            'available_days', 'shift_start', 'shift_end'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Interventional Cardiologist'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBBS, MD, FACC'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Room 102'}),
            'avg_consultation_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 60}),
            'daily_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Monday,Tuesday,Wednesday...'}),
            'shift_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'shift_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone_number'].initial = self.instance.user.phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
            profile.user.phone_number = self.cleaned_data['phone_number']
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile
