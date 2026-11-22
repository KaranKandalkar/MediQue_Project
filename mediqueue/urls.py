from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from doctors.models import Department, DoctorProfile
from queue_management.models import QueueToken
from django.utils import timezone


def home_view(request):
    """Modern Hospital Landing Page with quick access to portals and live queue display."""
    today = timezone.localdate()
    departments = Department.objects.filter(is_active=True)[:6]
    available_doctors_count = DoctorProfile.objects.filter(is_available=True).count()
    active_tokens_today = QueueToken.objects.filter(
        token_date=today,
        status__in=[QueueToken.Status.WAITING, QueueToken.Status.IN_CONSULTATION]
    ).count()

    return render(request, 'home.html', {
        'departments': departments,
        'available_doctors_count': available_doctors_count,
        'active_tokens_today': active_tokens_today,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('hospital-resources/', include('hospital_resources.urls')),
    path('appointments/', include('appointments.urls')),
    path('queue/', include('queue_management.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
