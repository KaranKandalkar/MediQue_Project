from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'user', 'gender', 'blood_group', 'date_of_birth', 'emergency_contact', 'created_at')
    search_fields = ('patient_id', 'user__first_name', 'user__last_name', 'user__username', 'emergency_contact')
    list_filter = ('gender', 'blood_group')
