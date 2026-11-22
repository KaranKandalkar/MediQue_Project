from django.urls import path
from . import views

app_name = 'hospital_resources'

urlpatterns = [
    path('', views.resource_list, name='resource_list'),
    path('add/', views.resource_create, name='resource_create'),
    path('<int:pk>/edit/', views.resource_update, name='resource_update'),
    path('<int:pk>/toggle-status/', views.resource_toggle_status, name='toggle_status'),
]
