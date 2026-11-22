from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import QueueToken, Consultation, Notification
from .forms import WalkInTokenForm, EmergencyPriorityForm, ConsultationForm
from .services import (
    generate_queue_token,
    get_doctor_queue,
    call_next_patient,
    start_consultation,
    complete_consultation,
    assign_emergency_priority,
    get_lobby_display_board,
)
from doctors.models import DoctorProfile, Department
from accounts.models import CustomUser
from accounts.decorators import staff_required, doctor_required


@login_required
def live_queue_list(request):
    dept_id = request.GET.get('department')
    doctor_id = request.GET.get('doctor')
    today = timezone.localdate()

    tokens = QueueToken.objects.filter(token_date=today).select_related('patient', 'doctor__user', 'department')

    if dept_id:
        tokens = tokens.filter(department_id=dept_id)
    if doctor_id:
        tokens = tokens.filter(doctor_id=doctor_id)

    departments = Department.objects.filter(is_active=True)
    doctors = DoctorProfile.objects.filter(is_available=True).select_related('user', 'department')

    waiting_tokens = tokens.filter(status=QueueToken.Status.WAITING).order_by('priority', 'token_sequence')
    active_tokens = tokens.filter(status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION])
    completed_tokens = tokens.filter(status=QueueToken.Status.COMPLETED).order_by('-completed_at')

    return render(request, 'queue_management/live_queue.html', {
        'waiting_tokens': waiting_tokens,
        'active_tokens': active_tokens,
        'completed_tokens': completed_tokens,
        'departments': departments,
        'doctors': doctors,
        'selected_dept': int(dept_id) if dept_id and dept_id.isdigit() else None,
        'selected_doc': int(doctor_id) if doctor_id and doctor_id.isdigit() else None,
        'today': today,
    })


@staff_required
def token_create(request):
    initial_data = {}
    patient_id = request.GET.get('patient_id')
    if patient_id and patient_id.isdigit():
        patient = CustomUser.objects.filter(pk=patient_id, role=CustomUser.Role.PATIENT).first()
        if patient:
            initial_data['patient'] = patient

    if request.method == 'POST':
        form = WalkInTokenForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            patient = form.cleaned_data['patient']
            department = form.cleaned_data['department']
            priority = form.cleaned_data['priority']
            priority_notes = form.cleaned_data['priority_notes']

            # Check if patient already has an active token for this doctor today
            existing = QueueToken.objects.filter(
                patient=patient,
                doctor=doctor,
                token_date=timezone.localdate(),
                status__in=[QueueToken.Status.WAITING, QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
            ).first()

            if existing:
                messages.warning(request, f"Patient {patient.display_name} already has active token #{existing.token_number} for Dr. {doctor.full_name} today.")
                return redirect('queue_management:token_detail', pk=existing.pk)

            token = generate_queue_token(
                doctor=doctor,
                patient=patient,
                department=department,
                priority=priority,
                assigned_by=request.user if priority == QueueToken.Priority.EMERGENCY else None,
                priority_notes=priority_notes
            )

            messages.success(request, f"Token #{token.token_number} generated successfully for {patient.display_name}!")
            return redirect('queue_management:token_detail', pk=token.pk)
    else:
        form = WalkInTokenForm(initial=initial_data)

    return render(request, 'queue_management/token_create.html', {'form': form})


@login_required
def token_detail(request, pk):
    token = get_object_or_404(
        QueueToken.objects.select_related('patient', 'doctor__user', 'department', 'appointment'),
        pk=pk
    )

    # Permission: staff or the patient themselves
    if not (request.user.is_admin_role or request.user.is_doctor_role or request.user.is_receptionist_role):
        if request.user != token.patient:
            messages.error(request, "Permission denied.")
            return redirect('dashboard:patient')

    position, est_wait = token.calculate_position_and_wait_time()

    current_token = QueueToken.objects.filter(
        doctor=token.doctor,
        token_date=token.token_date,
        status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
    ).first()

    emergency_form = EmergencyPriorityForm()

    return render(request, 'queue_management/token_detail.html', {
        'token': token,
        'position': position,
        'est_wait': est_wait,
        'current_token': current_token,
        'emergency_form': emergency_form,
    })


@staff_required
@require_POST
def token_cancel(request, pk):
    token = get_object_or_404(QueueToken, pk=pk)
    if token.status in [QueueToken.Status.COMPLETED, QueueToken.Status.CANCELLED]:
        messages.warning(request, "This token has already concluded.")
    else:
        token.status = QueueToken.Status.CANCELLED
        token.save(update_fields=['status'])
        messages.success(request, f"Token #{token.token_number} cancelled.")
    return redirect('queue_management:live_queue')


@staff_required
@require_POST
def assign_emergency(request, pk):
    token = get_object_or_404(QueueToken, pk=pk)
    form = EmergencyPriorityForm(request.POST)
    if form.is_valid():
        reason = form.cleaned_data['reason']
        assign_emergency_priority(token, request.user, reason)
        messages.success(request, f"Token #{token.token_number} priority elevated to EMERGENCY!")
    else:
        messages.error(request, "Please specify a clinical justification for emergency priority.")
    return redirect('queue_management:token_detail', pk=token.pk)


@doctor_required
@require_POST
def doctor_call_next(request):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    token = call_next_patient(doctor)
    if token:
        messages.success(request, f"Called Patient: Token #{token.token_number} ({token.patient.display_name}).")
    else:
        messages.info(request, "There are currently no waiting patients in your queue.")
    return redirect('dashboard:doctor')


@doctor_required
@require_POST
def doctor_start_consultation(request, pk):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    token = get_object_or_404(QueueToken, pk=pk, doctor=doctor)
    start_consultation(token)
    messages.success(request, f"Consultation started for Token #{token.token_number}.")
    return redirect('dashboard:doctor')


@doctor_required
def doctor_complete_consultation(request, pk):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    token = get_object_or_404(QueueToken, pk=pk, doctor=doctor)

    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            symptoms = form.cleaned_data['symptoms']
            diagnosis = form.cleaned_data['diagnosis']
            prescription = form.cleaned_data['prescription']
            follow_up_date = form.cleaned_data.get('follow_up_date')
            notes = form.cleaned_data.get('notes', '')

            vital_signs = {
                'bp': form.cleaned_data.get('bp', ''),
                'pulse': form.cleaned_data.get('pulse', ''),
                'temperature': form.cleaned_data.get('temperature', ''),
                'spo2': form.cleaned_data.get('spo2', ''),
            }

            consultation = complete_consultation(
                token=token,
                symptoms=symptoms,
                diagnosis=diagnosis,
                prescription=prescription,
                vital_signs=vital_signs,
                follow_up_date=follow_up_date,
                notes=notes
            )
            messages.success(request, f"Consultation completed for Token #{token.token_number}. Clinical record saved.")
            return redirect('dashboard:doctor')
    else:
        # Prepopulate symptoms from appointment if available
        init = {}
        if token.appointment:
            init['symptoms'] = token.appointment.reason
        form = ConsultationForm(initial=init)

    patient_profile = getattr(token.patient, 'patient_profile', None)

    return render(request, 'queue_management/consultation_form.html', {
        'form': form,
        'token': token,
        'patient_profile': patient_profile,
    })


@doctor_required
@require_POST
def doctor_skip_patient(request, pk):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    token = get_object_or_404(QueueToken, pk=pk, doctor=doctor)
    token.status = QueueToken.Status.SKIPPED
    token.save(update_fields=['status'])
    messages.warning(request, f"Token #{token.token_number} marked as SKIPPED.")
    return redirect('dashboard:doctor')


def public_display_board(request):
    """
    Public Lobby Display Screen (Waiting room TV monitor view).
    Accessible without login.
    """
    board_data = get_lobby_display_board()
    return render(request, 'queue_management/display_board.html', {
        'board_data': board_data,
        'now': timezone.now(),
    })


# API Views for Real-Time polling / dynamic updates
def api_lobby_board(request):
    board_data = get_lobby_display_board()
    return JsonResponse({'status': 'success', 'data': board_data, 'updated_at': timezone.now().strftime('%H:%M:%S')})


def api_queue_status(request):
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id or not doctor_id.isdigit():
        return JsonResponse({'error': 'Doctor ID required'}, status=400)

    doctor = get_object_or_404(DoctorProfile, pk=doctor_id)
    queue_data = get_doctor_queue(doctor)

    data = {
        'current_token': {
            'number': queue_data['current_token'].token_number,
            'status': queue_data['current_token'].get_status_display(),
            'patient_name': queue_data['current_token'].patient.display_name,
            'is_emergency': queue_data['current_token'].is_emergency,
        } if queue_data['current_token'] else None,
        'waiting_count': queue_data['waiting_count'],
        'completed_count': queue_data['completed_count'],
        'waiting_list': [
            {
                'id': t.id,
                'token_number': t.token_number,
                'patient_name': t.patient.display_name,
                'position': t.current_pos,
                'wait_time': t.calc_wait_time,
                'is_emergency': t.is_emergency,
            }
            for t in queue_data['waiting_list']
        ]
    }
    return JsonResponse({'status': 'success', 'data': data})


@login_required
def api_patient_token_status(request):
    token_id = request.GET.get('token_id')
    if not token_id or not token_id.isdigit():
        return JsonResponse({'error': 'Token ID required'}, status=400)

    token = get_object_or_404(QueueToken, pk=token_id)
    if not (request.user.is_staff or request.user == token.patient):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    pos, wait = token.calculate_position_and_wait_time()
    current = QueueToken.objects.filter(
        doctor=token.doctor,
        token_date=token.token_date,
        status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
    ).first()

    return JsonResponse({
        'status': 'success',
        'token_number': token.token_number,
        'token_status': token.get_status_display(),
        'position': pos,
        'estimated_wait_time': wait,
        'current_serving_token': current.token_number if current else None,
        'doctor_name': token.doctor.full_name,
        'room_number': token.doctor.room_number,
        'is_emergency': token.is_emergency,
    })
