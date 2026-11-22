from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('doctor/', views.doctor_dashboard, name='doctor'),
    path('receptionist/', views.receptionist_dashboard, name='receptionist'),
    path('patient/', views.patient_dashboard, name='patient'),
]
