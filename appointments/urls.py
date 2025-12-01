from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('create/', views.appointment_create, name='appointment_create'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/edit/', views.appointment_edit, name='appointment_edit'),
    path('<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
    path('<int:pk>/confirm-completion/', views.confirm_completion, name='confirm_completion'),
    path('<int:pk>/rate/', views.rate_appointment, name='rate_appointment'),
    path('<int:pk>/messages/', views.appointment_messages, name='appointment_messages'),
    path('history/completed/', views.completed_history, name='completed_history'),
    path('<int:pk>/receipt/', views.download_receipt, name='download_receipt'),
]