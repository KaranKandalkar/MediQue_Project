from django.contrib import admin
from .models import HospitalResource


@admin.register(HospitalResource)
class HospitalResourceAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'name', 'resource_type', 'department', 'assigned_doctor', 'status', 'capacity')
    list_filter = ('resource_type', 'status', 'department')
    search_fields = ('room_number', 'name')
