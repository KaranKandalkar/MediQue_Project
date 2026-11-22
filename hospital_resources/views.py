from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import HospitalResource
from .forms import HospitalResourceForm
from accounts.decorators import staff_required, admin_required


@staff_required
def resource_list(request):
    res_type = request.GET.get('type')
    status = request.GET.get('status')

    resources = HospitalResource.objects.select_related('department', 'assigned_doctor__user').all()

    if res_type:
        resources = resources.filter(resource_type=res_type)
    if status:
        resources = resources.filter(status=status)

    available_count = HospitalResource.objects.filter(status=HospitalResource.Status.AVAILABLE).count()
    occupied_count = HospitalResource.objects.filter(status=HospitalResource.Status.OCCUPIED).count()
    maintenance_count = HospitalResource.objects.filter(status=HospitalResource.Status.MAINTENANCE).count()

    return render(request, 'hospital_resources/resource_list.html', {
        'resources': resources,
        'types': HospitalResource.ResourceType.choices,
        'statuses': HospitalResource.Status.choices,
        'selected_type': res_type,
        'selected_status': status,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'maintenance_count': maintenance_count,
    })


@admin_required
def resource_create(request):
    if request.method == 'POST':
        form = HospitalResourceForm(request.POST)
        if form.is_valid():
            res = form.save()
            messages.success(request, f"Resource {res.room_number} ({res.name}) added successfully.")
            return redirect('hospital_resources:resource_list')
    else:
        form = HospitalResourceForm()

    return render(request, 'hospital_resources/resource_form.html', {'form': form, 'is_create': True})


@admin_required
def resource_update(request, pk):
    resource = get_object_or_404(HospitalResource, pk=pk)
    if request.method == 'POST':
        form = HospitalResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"Resource {resource.room_number} updated.")
            return redirect('hospital_resources:resource_list')
    else:
        form = HospitalResourceForm(instance=resource)

    return render(request, 'hospital_resources/resource_form.html', {'form': form, 'resource': resource, 'is_create': False})


@staff_required
@require_POST
def resource_toggle_status(request, pk):
    resource = get_object_or_404(HospitalResource, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(HospitalResource.Status.choices):
        resource.status = new_status
        resource.save(update_fields=['status'])
        return JsonResponse({
            'success': True,
            'room_number': resource.room_number,
            'status': resource.status,
            'status_display': resource.get_status_display()
        })
    return JsonResponse({'error': 'Invalid status'}, status=400)
