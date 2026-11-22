from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:pk>/check-in/', views.check_in_appointment, name='check_in'),
]
