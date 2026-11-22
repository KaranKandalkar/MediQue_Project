from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Appointment
from .forms import AppointmentBookingForm
from accounts.models import CustomUser
from doctors.models import DoctorProfile, Department
from queue_management.services import generate_queue_token
from queue_management.models import QueueToken


@login_required
def appointment_list(request):
    user = request.user
    today = timezone.localdate()

    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    dept_filter = request.GET.get('department')

    if user.is_patient_role:
        appointments = Appointment.objects.filter(patient=user)
    elif user.is_doctor_role and hasattr(user, 'doctor_profile'):
        appointments = Appointment.objects.filter(doctor=user.doctor_profile)
    else:
        # Admin or Receptionist sees all
        appointments = Appointment.objects.all()

    appointments = appointments.select_related('patient', 'doctor__user', 'department')

    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    if dept_filter:
        appointments = appointments.filter(department_id=dept_filter)

    departments = Department.objects.filter(is_active=True)

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'departments': departments,
        'statuses': Appointment.Status.choices,
        'selected_status': status_filter,
        'selected_date': date_filter,
        'selected_dept': int(dept_filter) if dept_filter and dept_filter.isdigit() else None,
        'today': today,
    })


@login_required
def book_appointment(request):
    user = request.user
    patient_user = user

    # If staff is booking on behalf of a patient
    patient_id = request.GET.get('patient_id') or request.POST.get('patient_user_id')
    if (user.is_admin_role or user.is_receptionist_role) and patient_id:
        patient_user = get_object_or_404(CustomUser, pk=patient_id, role=CustomUser.Role.PATIENT)

    # Pre-select doctor if passed in query string
    pre_doc_id = request.GET.get('doctor_id')
    initial_data = {}
    if pre_doc_id and pre_doc_id.isdigit():
        pre_doc = DoctorProfile.objects.filter(pk=pre_doc_id).first()
        if pre_doc:
            initial_data['doctor'] = pre_doc
            initial_data['department'] = pre_doc.department

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient_user
            appointment.save()

            messages.success(
                request,
                f"Appointment booked successfully with Dr. {appointment.doctor.full_name} on {appointment.appointment_date} at {appointment.appointment_time.strftime('%H:%M')}."
            )

            # If appointment is for today, give option to generate token immediately
            if appointment.appointment_date == timezone.localdate():
                token = generate_queue_token(
                    doctor=appointment.doctor,
                    patient=appointment.patient,
                    department=appointment.department,
                    appointment=appointment,
                    assigned_by=user if user != patient_user else None
                )
                messages.info(request, f"Today's queue token #{token.token_number} generated automatically!")

            if user.is_patient_role:
                return redirect('dashboard:patient')
            elif user.is_receptionist_role:
                return redirect('dashboard:receptionist')
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentBookingForm(initial=initial_data)

    patients_list = None
    if user.is_admin_role or user.is_receptionist_role:
        patients_list = CustomUser.objects.filter(role=CustomUser.Role.PATIENT).select_related('patient_profile')

    return render(request, 'appointments/book_appointment.html', {
        'form': form,
        'patient_user': patient_user,
        'patients_list': patients_list,
        'is_staff_booking': (user.is_admin_role or user.is_receptionist_role),
    })


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Permissions
    if not (request.user.is_admin_role or request.user.is_receptionist_role or request.user == appointment.patient):
        messages.error(request, "Permission denied.")
        return redirect('appointments:appointment_list')

    if not appointment.is_cancellable:
        messages.error(request, "Only upcoming scheduled appointments can be cancelled.")
        return redirect('appointments:appointment_list')

    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=['status'])

    # Cancel associated active token if one was issued
    QueueToken.objects.filter(appointment=appointment, status=QueueToken.Status.WAITING).update(
        status=QueueToken.Status.CANCELLED
    )

    messages.success(request, f"Appointment #{appointment.id} has been cancelled successfully.")
    if request.user.is_patient_role:
        return redirect('dashboard:patient')
    return redirect('appointments:appointment_list')


@login_required
def check_in_appointment(request, pk):
    """Receptionist or Staff checks in patient upon arrival and generates daily token."""
    if not (request.user.is_admin_role or request.user.is_receptionist_role):
        messages.error(request, "Only receptionists or administrators can perform check-in.")
        return redirect('dashboard:index')

    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.appointment_date != timezone.localdate():
        messages.warning(request, f"This appointment is scheduled for {appointment.appointment_date}, not today.")

    # Check if token already exists for today
    existing_token = QueueToken.objects.filter(appointment=appointment, token_date=timezone.localdate()).first()
    if existing_token:
        messages.info(request, f"Token #{existing_token.token_number} has already been issued for this appointment.")
        return redirect('queue_management:token_detail', pk=existing_token.pk)

    token = generate_queue_token(
        doctor=appointment.doctor,
        patient=appointment.patient,
        department=appointment.department,
        appointment=appointment,
        assigned_by=request.user
    )

    messages.success(request, f"Patient checked in! Token #{token.token_number} generated.")
    return redirect('queue_management:token_detail', pk=token.pk)
