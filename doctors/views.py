from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import DoctorProfile, Department
from .forms import DoctorProfileForm, DepartmentForm
from accounts.models import CustomUser
from accounts.decorators import admin_required, doctor_required, staff_required


def doctor_list(request):
    dept_id = request.GET.get('department')
    search_query = request.GET.get('q', '').strip()

    doctors = DoctorProfile.objects.select_related('user', 'department').all()

    if dept_id:
        doctors = doctors.filter(department_id=dept_id)
    if search_query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )

    departments = Department.objects.filter(is_active=True)

    return render(request, 'doctors/doctor_list.html', {
        'doctors': doctors,
        'departments': departments,
        'selected_dept': int(dept_id) if dept_id and dept_id.isdigit() else None,
        'search_query': search_query,
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(DoctorProfile.objects.select_related('user', 'department'), pk=pk)
    return render(request, 'doctors/doctor_detail.html', {'doctor': doctor})


@admin_required
def doctor_create(request):
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Username and initial password are required for new doctors.")
            return render(request, 'doctors/doctor_form.html', {'form': form, 'is_create': True})

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "A user with that username already exists.")
            return render(request, 'doctors/doctor_form.html', {'form': form, 'is_create': True})

        if form.is_valid():
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                role=CustomUser.Role.DOCTOR,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number']
            )
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, f"Doctor {user.display_name} has been added successfully.")
            return redirect('doctors:doctor_list')
    else:
        form = DoctorProfileForm()

    return render(request, 'doctors/doctor_form.html', {'form': form, 'is_create': True})


@admin_required
def doctor_update(request, pk):
    doctor = get_object_or_404(DoctorProfile, pk=pk)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dr. {doctor.user.display_name}'s profile has been updated.")
            return redirect('doctors:doctor_list')
    else:
        form = DoctorProfileForm(instance=doctor)

    return render(request, 'doctors/doctor_form.html', {'form': form, 'doctor': doctor, 'is_create': False})


@login_required
@require_POST
def toggle_availability(request, pk):
    doctor = get_object_or_404(DoctorProfile, pk=pk)
    # Check permissions: doctor themselves or admin/receptionist
    if not (request.user.is_admin_role or request.user.is_receptionist_role or (hasattr(request.user, 'doctor_profile') and request.user.doctor_profile.id == doctor.id)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    doctor.is_available = not doctor.is_available
    doctor.save(update_fields=['is_available'])
    return JsonResponse({
        'success': True,
        'doctor_id': doctor.id,
        'is_available': doctor.is_available,
        'status_text': 'Available' if doctor.is_available else 'On Break / Unavailable'
    })


@staff_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'doctors/department_list.html', {'departments': departments})


@admin_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect('doctors:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'doctors/department_form.html', {'form': form, 'is_create': True})


@admin_required
def department_update(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect('doctors:department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'doctors/department_form.html', {'form': form, 'department': dept, 'is_create': False})


def api_doctors_by_department(request):
    dept_id = request.GET.get('department_id')
    doctors = DoctorProfile.objects.filter(is_available=True)
    if dept_id:
        doctors = doctors.filter(department_id=dept_id)

    data = [
        {
            'id': doc.id,
            'name': doc.full_name,
            'specialization': doc.specialization,
            'fee': float(doc.consultation_fee),
            'room': doc.room_number,
            'avg_time': doc.avg_consultation_time,
        }
        for doc in doctors
    ]
    return JsonResponse({'doctors': data})
