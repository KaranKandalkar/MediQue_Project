from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
import json

from accounts.models import CustomUser
from accounts.decorators import admin_required, doctor_required, receptionist_required, patient_required
from doctors.models import DoctorProfile, Department
from patients.models import PatientProfile
from appointments.models import Appointment
from queue_management.models import QueueToken, Consultation
from queue_management.services import get_doctor_queue
from hospital_resources.models import HospitalResource


@login_required
def index(request):
    """Dispatches user to their designated role dashboard."""
    user = request.user
    if user.is_superuser or user.role == CustomUser.Role.ADMIN:
        return redirect('dashboard:admin')
    elif user.role == CustomUser.Role.DOCTOR:
        return redirect('dashboard:doctor')
    elif user.role == CustomUser.Role.RECEPTIONIST:
        return redirect('dashboard:receptionist')
    elif user.role == CustomUser.Role.PATIENT:
        return redirect('dashboard:patient')
    return redirect('accounts:login')


@admin_required
def admin_dashboard(request):
    today = timezone.localdate()
    
    # High-level KPIs
    total_patients = PatientProfile.objects.count()
    total_doctors = DoctorProfile.objects.count()
    active_doctors = DoctorProfile.objects.filter(is_available=True).count()
    
    today_appointments = Appointment.objects.filter(appointment_date=today)
    today_appointments_count = today_appointments.count()
    today_completed_appointments = today_appointments.filter(status=Appointment.Status.COMPLETED).count()
    today_cancelled_appointments = today_appointments.filter(status=Appointment.Status.CANCELLED).count()

    today_tokens = QueueToken.objects.filter(token_date=today)
    waiting_tokens_count = today_tokens.filter(status=QueueToken.Status.WAITING).count()
    in_consultation_count = today_tokens.filter(status=QueueToken.Status.IN_CONSULTATION).count()
    completed_tokens_count = today_tokens.filter(status=QueueToken.Status.COMPLETED).count()

    # Average wait time
    completed_today_tokens = today_tokens.filter(status=QueueToken.Status.COMPLETED, called_at__isnull=False)
    wait_times = []
    for t in completed_today_tokens:
        diff = (t.called_at - t.created_at).total_seconds() / 60
        if 0 <= diff <= 300:
            wait_times.append(diff)
    avg_wait_time = round(sum(wait_times) / len(wait_times)) if wait_times else 14

    # Department-wise breakdown for Chart.js
    departments = Department.objects.filter(is_active=True).annotate(
        appointment_count=Count('appointments', filter=Q(appointments__appointment_date=today)),
        token_count=Count('queue_tokens', filter=Q(queue_tokens__token_date=today))
    )
    dept_labels = [d.name for d in departments]
    dept_app_counts = [d.appointment_count for d in departments]
    dept_token_counts = [d.token_count for d in departments]

    # 7-day appointment trend
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    trend_labels = [d.strftime('%b %d') for d in last_7_days]
    trend_counts = [
        Appointment.objects.filter(appointment_date=d).count()
        for d in last_7_days
    ]

    # Hospital Resources
    total_resources = HospitalResource.objects.count()
    available_resources = HospitalResource.objects.filter(status=HospitalResource.Status.AVAILABLE).count()
    occupied_resources = HospitalResource.objects.filter(status=HospitalResource.Status.OCCUPIED).count()
    maintenance_resources = HospitalResource.objects.filter(status=HospitalResource.Status.MAINTENANCE).count()

    # Recent activity
    recent_tokens = today_tokens.select_related('patient', 'doctor__user', 'department').order_by('-created_at')[:8]

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'active_doctors': active_doctors,
        'today_appointments_count': today_appointments_count,
        'today_completed_appointments': today_completed_appointments,
        'today_cancelled_appointments': today_cancelled_appointments,
        'waiting_tokens_count': waiting_tokens_count,
        'in_consultation_count': in_consultation_count,
        'completed_tokens_count': completed_tokens_count,
        'avg_wait_time': avg_wait_time,
        'total_resources': total_resources,
        'available_resources': available_resources,
        'occupied_resources': occupied_resources,
        'maintenance_resources': maintenance_resources,
        'recent_tokens': recent_tokens,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_app_counts_json': json.dumps(dept_app_counts),
        'dept_token_counts_json': json.dumps(dept_token_counts),
        'trend_labels_json': json.dumps(trend_labels),
        'trend_counts_json': json.dumps(trend_counts),
    })


@doctor_required
def doctor_dashboard(request):
    doctor = get_object_or_404(DoctorProfile.objects.select_related('department', 'user'), user=request.user)
    today = timezone.localdate()

    queue_data = get_doctor_queue(doctor, today)
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).select_related('patient').order_by('appointment_time')

    recent_consultations = Consultation.objects.filter(
        doctor=doctor
    ).select_related('patient', 'token').order_by('-start_time')[:5]

    return render(request, 'dashboard/doctor_dashboard.html', {
        'doctor': doctor,
        'current_token': queue_data['current_token'],
        'waiting_list': queue_data['waiting_list'],
        'completed_list': queue_data['completed_list'],
        'waiting_count': queue_data['waiting_count'],
        'completed_count': queue_data['completed_count'],
        'total_count': queue_data['total_count'],
        'today_appointments': today_appointments,
        'recent_consultations': recent_consultations,
        'today': today,
    })


@receptionist_required
def receptionist_dashboard(request):
    today = timezone.localdate()

    today_appointments = Appointment.objects.filter(
        appointment_date=today
    ).select_related('patient', 'doctor__user', 'department').order_by('appointment_time')

    active_tokens = QueueToken.objects.filter(
        token_date=today,
        status__in=[QueueToken.Status.WAITING, QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
    ).select_related('patient', 'doctor__user', 'department').order_by('priority', 'token_sequence')

    doctors = DoctorProfile.objects.select_related('user', 'department').all()
    departments = Department.objects.filter(is_active=True).annotate(
        active_tokens_count=Count('queue_tokens', filter=Q(queue_tokens__token_date=today, queue_tokens__status__in=[
            QueueToken.Status.WAITING, QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION
        ]))
    )

    total_tokens_today = QueueToken.objects.filter(token_date=today).count()
    waiting_tokens_today = QueueToken.objects.filter(token_date=today, status=QueueToken.Status.WAITING).count()
    emergency_tokens_today = QueueToken.objects.filter(
        token_date=today,
        priority=QueueToken.Priority.EMERGENCY,
        status=QueueToken.Status.WAITING
    ).count()

    return render(request, 'dashboard/receptionist_dashboard.html', {
        'today_appointments': today_appointments,
        'active_tokens': active_tokens,
        'doctors': doctors,
        'departments': departments,
        'total_tokens_today': total_tokens_today,
        'waiting_tokens_today': waiting_tokens_today,
        'emergency_tokens_today': emergency_tokens_today,
        'today': today,
    })


@patient_required
def patient_dashboard(request):
    user = request.user
    today = timezone.localdate()

    patient_profile = getattr(user, 'patient_profile', None)

    # Active tokens for today
    active_tokens = QueueToken.objects.filter(
        patient=user,
        token_date=today,
        status__in=[QueueToken.Status.WAITING, QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
    ).select_related('doctor__user', 'doctor__department')

    tokens_with_info = []
    for tok in active_tokens:
        pos, est_wait = tok.calculate_position_and_wait_time()
        current_serving = QueueToken.objects.filter(
            doctor=tok.doctor,
            token_date=today,
            status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
        ).first()

        tokens_with_info.append({
            'token': tok,
            'position': pos,
            'est_wait': est_wait,
            'current_serving': current_serving.token_number if current_serving else "None",
        })

    # Upcoming Appointments
    upcoming_appointments = Appointment.objects.filter(
        patient=user,
        appointment_date__gte=today,
        status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CHECKED_IN]
    ).select_related('doctor__user', 'department').order_by('appointment_date', 'appointment_time')

    # Past Consultations / Prescriptions
    past_consultations = Consultation.objects.filter(
        patient=user
    ).select_related('doctor__user', 'doctor__department', 'token').order_by('-start_time')

    return render(request, 'dashboard/patient_dashboard.html', {
        'patient_profile': patient_profile,
        'active_tokens': tokens_with_info,
        'upcoming_appointments': upcoming_appointments,
        'past_consultations': past_consultations,
        'today': today,
    })
