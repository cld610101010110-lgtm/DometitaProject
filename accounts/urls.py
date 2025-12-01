from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Admin Doctor Management
    path('admin/doctors/create/', views.admin_create_doctor, name='admin_create_doctor'),
    path('admin/doctors/<int:doctor_id>/edit/', views.admin_edit_doctor, name='admin_edit_doctor'),
    
    # Admin Account Management
    path('admin/account/update/', views.admin_update_account, name='admin_update_account'),

    # Admin Appointments Management
    path('admin/appointments/', views.admin_appointments_list, name='admin_appointments_list'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
]