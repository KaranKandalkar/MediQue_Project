from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.crypto import get_random_string
from .models import PatientProfile
from .forms import WalkInPatientForm, PatientMedicalProfileForm
from accounts.models import CustomUser
from accounts.decorators import staff_required, patient_required
from appointments.models import Appointment
from queue_management.models import QueueToken, Consultation


@staff_required
def patient_list(request):
    q = request.GET.get('q', '').strip()
    patients = PatientProfile.objects.select_related('user').all()

    if q:
        patients = patients.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__phone_number__icontains=q) |
            Q(patient_id__icontains=q) |
            Q(user__email__icontains=q)
        )

    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'search_query': q,
    })


@login_required
def patient_detail(request, pk):
    patient_profile = get_object_or_404(PatientProfile.objects.select_related('user'), pk=pk)

    # Permission check: patient can only view their own record unless staff
    if not (request.user.is_admin_role or request.user.is_doctor_role or request.user.is_receptionist_role):
        if request.user != patient_profile.user:
            messages.error(request, "Access denied. You can only view your own records.")
            return redirect('dashboard:patient')

    appointments = Appointment.objects.filter(patient=patient_profile.user).order_by('-appointment_date')
    tokens = QueueToken.objects.filter(patient=patient_profile.user).order_by('-created_at')
    consultations = Consultation.objects.filter(patient=patient_profile.user).select_related('doctor__user', 'doctor__department').order_by('-start_time')

    return render(request, 'patients/patient_detail.html', {
        'patient': patient_profile,
        'appointments': appointments,
        'tokens': tokens,
        'consultations': consultations,
    })


@staff_required
def patient_create(request):
    if request.method == 'POST':
        form = WalkInPatientForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone = form.cleaned_data['phone_number']
            email = form.cleaned_data.get('email')

            # Create username from name/phone
            base_user = f"pat_{phone[-6:]}" if len(phone) >= 6 else f"pat_{get_random_string(6)}"
            username = base_user
            idx = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_user}_{idx}"
                idx += 1

            # Generate default secure password for walk-in
            temp_pass = get_random_string(10)
            user = CustomUser.objects.create_user(
                username=username,
                password=temp_pass,
                role=CustomUser.Role.PATIENT,
                first_name=first_name,
                last_name=last_name,
                email=email or f"{username}@hospital.local",
                phone_number=phone
            )

            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            messages.success(request, f"Patient {user.display_name} registered with ID {profile.patient_id}.")
            # Option to immediately generate token
            generate_token = request.POST.get('generate_token')
            if generate_token:
                return redirect(f"/queue/tokens/create/?patient_id={user.id}")
            return redirect('patients:patient_detail', pk=profile.pk)
    else:
        form = WalkInPatientForm()

    return render(request, 'patients/patient_create.html', {'form': form})


@login_required
def patient_update(request, pk):
    patient_profile = get_object_or_404(PatientProfile, pk=pk)

    # Permission check
    if not (request.user.is_admin_role or request.user.is_doctor_role or request.user.is_receptionist_role or request.user == patient_profile.user):
        messages.error(request, "Permission denied.")
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = PatientMedicalProfileForm(request.POST, instance=patient_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Medical profile information updated successfully.")
            return redirect('patients:patient_detail', pk=patient_profile.pk)
    else:
        form = PatientMedicalProfileForm(instance=patient_profile)

    return render(request, 'patients/patient_form.html', {
        'form': form,
        'patient': patient_profile
    })
