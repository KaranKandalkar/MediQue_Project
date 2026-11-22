from django.urls import path
from . import views

app_name = 'queue_management'

urlpatterns = [
    path('', views.live_queue_list, name='live_queue'),
    path('tokens/create/', views.token_create, name='token_create'),
    path('tokens/<int:pk>/', views.token_detail, name='token_detail'),
    path('tokens/<int:pk>/cancel/', views.token_cancel, name='token_cancel'),
    path('tokens/<int:pk>/assign-emergency/', views.assign_emergency, name='assign_emergency'),
    path('doctor/call-next/', views.doctor_call_next, name='doctor_call_next'),
    path('doctor/start/<int:pk>/', views.doctor_start_consultation, name='doctor_start_consultation'),
    path('doctor/complete/<int:pk>/', views.doctor_complete_consultation, name='doctor_complete_consultation'),
    path('doctor/skip/<int:pk>/', views.doctor_skip_patient, name='doctor_skip_patient'),
    path('display/', views.public_display_board, name='public_display_board'),
    
    # APIs for real-time polling
    path('api/lobby-board/', views.api_lobby_board, name='api_lobby_board'),
    path('api/queue-status/', views.api_queue_status, name='api_queue_status'),
    path('api/patient-token-status/', views.api_patient_token_status, name='api_patient_token_status'),
]
