from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),  # Public doctor list
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('dashboard/', views.doctor_dashboard, name='dashboard'),  # Doctor's own dashboard
    path('appointments/', views.doctor_appointments, name='appointments'),
    path('patients/', views.doctor_patients, name='patients'),
    path('ratings/', views.doctor_ratings_feedback, name='ratings_feedback'),
    path('appointment/<int:appointment_id>/<str:action>/', views.appointment_action, name='appointment_action'),
]