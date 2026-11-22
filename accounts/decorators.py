from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator for views that checks whether the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            # Superuser can access everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access that area.")
            return redirect('dashboard:index')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['ADMIN'])(view_func)


def doctor_required(view_func):
    return role_required(['DOCTOR'])(view_func)


def receptionist_required(view_func):
    return role_required(['RECEPTIONIST', 'ADMIN'])(view_func)


def patient_required(view_func):
    return role_required(['PATIENT'])(view_func)


def staff_required(view_func):
    """Allows Admin, Doctor, or Receptionist access."""
    return role_required(['ADMIN', 'DOCTOR', 'RECEPTIONIST'])(view_func)
