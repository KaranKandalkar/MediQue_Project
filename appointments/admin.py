from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'department', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'department')
    search_fields = ('patient__username', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    date_hierarchy = 'appointment_date'
