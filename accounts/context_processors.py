def user_role_context(request):
    """Context processor providing user role and hospital identity across templates."""
    context = {
        'APP_NAME': 'MediQueue',
        'HOSPITAL_NAME': 'MetroCare General Hospital',
    }
    
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_role': user.role,
            'is_admin': user.is_admin_role,
            'is_doctor': user.is_doctor_role,
            'is_receptionist': user.is_receptionist_role,
            'is_patient': user.is_patient_role,
            'unread_notifications_count': getattr(user, 'notifications', None).filter(is_read=False).count() if hasattr(user, 'notifications') else 0,
        })
    return context
