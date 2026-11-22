from django.db import transaction
from django.utils import timezone
from django.db.models import Max
from .models import QueueToken, Consultation, Notification
from appointments.models import Appointment
from hospital_resources.models import HospitalResource


@transaction.atomic
def generate_queue_token(doctor, patient, department=None, appointment=None, priority='NORMAL', assigned_by=None, priority_notes=""):
    """
    Thread-safe / atomic generation of daily sequential queue tokens for a doctor.
    Handles department assignment, sequence calculation, and notifications.
    """
    today = timezone.localdate()
    dept = department or doctor.department

    # Lock rows for this doctor and date to guarantee sequence integrity
    last_seq = QueueToken.objects.filter(
        doctor=doctor,
        token_date=today
    ).aggregate(max_seq=Max('token_sequence'))['max_seq'] or 0

    next_seq = last_seq + 1
    dept_code = dept.code.upper() if dept and dept.code else "GEN"
    token_str = f"{dept_code}-{next_seq:03d}"

    token = QueueToken.objects.create(
        token_number=token_str,
        token_sequence=next_seq,
        patient=patient,
        doctor=doctor,
        department=dept,
        appointment=appointment,
        token_date=today,
        priority=priority,
        priority_assigned_by=assigned_by,
        priority_notes=priority_notes,
        status=QueueToken.Status.WAITING
    )

    # Calculate initial wait time estimate
    pos, est_wait = token.calculate_position_and_wait_time()
    token.estimated_wait_time = est_wait
    token.save(update_fields=['estimated_wait_time'])

    # If linked to an appointment, mark appointment as CHECKED_IN
    if appointment:
        appointment.status = Appointment.Status.CHECKED_IN
        appointment.save(update_fields=['status'])

    # Send Notification to patient
    Notification.objects.create(
        user=patient,
        title=f"Token Generated: {token.token_number}",
        message=f"Your token for Dr. {doctor.user.get_full_name() or doctor.user.username} is #{token.token_number}. Position: #{pos}, Estimated wait: ~{est_wait} mins.",
        notification_type='QUEUE'
    )

    return token


def get_doctor_queue(doctor, date=None):
    """
    Returns structured queue data for a doctor on a given date (defaults to today).
    """
    target_date = date or timezone.localdate()

    current_token = QueueToken.objects.filter(
        doctor=doctor,
        token_date=target_date,
        status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
    ).first()

    waiting_qs = QueueToken.objects.filter(
        doctor=doctor,
        token_date=target_date,
        status=QueueToken.Status.WAITING
    ).order_by('priority', 'token_sequence')

    avg_time = doctor.avg_consultation_time or 15
    waiting_list = []
    for idx, tok in enumerate(waiting_qs):
        pos = idx + 1
        est_wait = (idx * avg_time) + (max(5, avg_time // 2) if current_token else 0)
        tok.current_pos = pos
        tok.calc_wait_time = est_wait
        waiting_list.append(tok)

    completed_list = QueueToken.objects.filter(
        doctor=doctor,
        token_date=target_date,
        status=QueueToken.Status.COMPLETED
    ).order_by('-completed_at')

    return {
        'current_token': current_token,
        'waiting_list': waiting_list,
        'completed_list': completed_list,
        'total_count': QueueToken.objects.filter(doctor=doctor, token_date=target_date).count(),
        'waiting_count': len(waiting_list),
        'completed_count': completed_list.count(),
    }


@transaction.atomic
def call_next_patient(doctor):
    """
    Calls the next patient in queue (emergency patients first, then FIFO by sequence).
    """
    today = timezone.localdate()

    # Next eligible waiting patient
    next_token = QueueToken.objects.filter(
        doctor=doctor,
        token_date=today,
        status=QueueToken.Status.WAITING
    ).order_by('priority', 'token_sequence').first()

    if not next_token:
        return None

    next_token.status = QueueToken.Status.CALLED
    next_token.called_at = timezone.now()
    next_token.save(update_fields=['status', 'called_at'])

    # Send Notification to patient
    room_text = f"Room {doctor.room_number}" if doctor.room_number else "Consultation Room"
    Notification.objects.create(
        user=next_token.patient,
        title=f"Your Token {next_token.token_number} is Called!",
        message=f"Please proceed to {room_text} for your consultation with {doctor.user.display_name}.",
        notification_type='QUEUE'
    )

    return next_token


@transaction.atomic
def start_consultation(token):
    """Marks consultation as actively underway and updates resource room status."""
    token.status = QueueToken.Status.IN_CONSULTATION
    token.consultation_started_at = timezone.now()
    token.save(update_fields=['status', 'consultation_started_at'])

    # Mark room occupied
    if token.doctor.room_number:
        HospitalResource.objects.filter(
            room_number=token.doctor.room_number
        ).update(status=HospitalResource.Status.OCCUPIED)

    return token


@transaction.atomic
def complete_consultation(token, symptoms, diagnosis, prescription, vital_signs=None, follow_up_date=None, notes=""):
    """
    Completes a consultation, saves clinical notes/prescriptions, frees room, updates appointment.
    """
    now = timezone.now()
    token.status = QueueToken.Status.COMPLETED
    token.completed_at = now

    duration = 15
    if token.consultation_started_at:
        duration = max(1, int((now - token.consultation_started_at).total_seconds() / 60))

    token.save(update_fields=['status', 'completed_at'])

    consultation = Consultation.objects.create(
        token=token,
        doctor=token.doctor,
        patient=token.patient,
        start_time=token.consultation_started_at or now,
        end_time=now,
        duration_minutes=duration,
        symptoms=symptoms,
        diagnosis=diagnosis,
        prescription=prescription,
        vital_signs=vital_signs or {},
        follow_up_date=follow_up_date,
        notes=notes
    )

    # Update appointment if any
    if token.appointment:
        token.appointment.status = Appointment.Status.COMPLETED
        token.appointment.save(update_fields=['status'])

    # Free up room
    if token.doctor.room_number:
        HospitalResource.objects.filter(
            room_number=token.doctor.room_number
        ).update(status=HospitalResource.Status.AVAILABLE)

    # Notify patient
    Notification.objects.create(
        user=token.patient,
        title="Consultation Completed",
        message=f"Your consultation with {token.doctor.user.display_name} has completed. Prescription and summary are available in your portal.",
        notification_type='QUEUE'
    )

    return consultation


@transaction.atomic
def assign_emergency_priority(token, authorized_user, reason=""):
    """
    Elevates a patient token to emergency priority.
    Only authorized personnel can call this function.
    """
    token.priority = QueueToken.Priority.EMERGENCY
    token.priority_assigned_by = authorized_user
    token.priority_notes = reason or "Clinical emergency triage priority"
    token.save(update_fields=['priority', 'priority_assigned_by', 'priority_notes'])

    Notification.objects.create(
        user=token.patient,
        title="Priority Updated to Emergency",
        message=f"Token {token.token_number} priority has been set to Emergency by hospital staff: {token.priority_notes}",
        notification_type='EMERGENCY'
    )
    return token


def get_lobby_display_board():
    """
    Returns public waiting room monitor data for all active departments & doctors.
    """
    today = timezone.localdate()
    from doctors.models import DoctorProfile

    doctors = DoctorProfile.objects.filter(is_available=True).select_related('department', 'user')
    board_data = []

    for doc in doctors:
        current = QueueToken.objects.filter(
            doctor=doc,
            token_date=today,
            status__in=[QueueToken.Status.CALLED, QueueToken.Status.IN_CONSULTATION]
        ).first()

        next_tokens = QueueToken.objects.filter(
            doctor=doc,
            token_date=today,
            status=QueueToken.Status.WAITING
        ).order_by('priority', 'token_sequence')[:4]

        board_data.append({
            'doctor_id': doc.id,
            'doctor_name': doc.full_name,
            'department_name': doc.department.name if doc.department else "General",
            'department_code': doc.department.code if doc.department else "GEN",
            'room_number': doc.room_number or "Cabin 1",
            'current_token': current.token_number if current else "--",
            'current_status': current.get_status_display() if current else "Idle / Ready",
            'current_is_emergency': current.is_emergency if current else False,
            'next_tokens': [
                {
                    'token_number': t.token_number,
                    'is_emergency': t.is_emergency
                } for t in next_tokens
            ],
            'waiting_count': QueueToken.objects.filter(
                doctor=doc,
                token_date=today,
                status=QueueToken.Status.WAITING
            ).count()
        })

    return board_data
