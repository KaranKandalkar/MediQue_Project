from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('add/', views.doctor_create, name='doctor_create'),
    path('<int:pk>/edit/', views.doctor_update, name='doctor_update'),
    path('<int:pk>/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_update, name='department_update'),
    path('api/by-department/', views.api_doctors_by_department, name='api_by_department'),
]
