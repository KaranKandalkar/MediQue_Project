from django.contrib import admin
from .models import Department, DoctorProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'specialization', 'room_number', 'is_available', 'avg_consultation_time', 'daily_capacity')
    list_filter = ('department', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'specialization', 'room_number')
