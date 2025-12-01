from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main Pages & Authentication
    path('', account_views.home_view, name='home'),
    path('profile/', account_views.profile_view, name='profile'),
    path('login/', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('logout/', account_views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/', account_views.patient_dashboard, name='patient_dashboard'),
    path('admin-dashboard/', account_views.admin_dashboard, name='admin_dashboard'),
    
    # Notifications
    path('notifications/', account_views.notification_list, name='notification_list'),

    # Include other app URLs
    path('', include('accounts.urls')),  # Include all accounts URLs
    path('appointments/', include('appointments.urls')),
    path('doctors/', include('doctors.urls')),
]