from django.contrib import admin
from .models import QueueToken, Consultation, Notification


@admin.register(QueueToken)
class QueueTokenAdmin(admin.ModelAdmin):
    list_display = ('token_number', 'patient', 'doctor', 'token_date', 'priority', 'status', 'token_sequence', 'estimated_wait_time')
    list_filter = ('token_date', 'priority', 'status', 'department')
    search_fields = ('token_number', 'patient__username', 'patient__first_name', 'patient__last_name', 'doctor__user__first_name')
    date_hierarchy = 'token_date'


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'doctor', 'patient', 'start_time', 'duration_minutes', 'diagnosis')
    search_fields = ('token__token_number', 'doctor__user__first_name', 'patient__username', 'diagnosis')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title', 'message')
