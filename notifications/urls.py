from django.urls import path
from . import views

urlpatterns = [
    # Notification list
    path('', views.notification_list, name='notification_list'),
    
    # Mark notifications as read
    path('<int:pk>/read/', views.mark_as_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_notifications_read'),
    
    # Delete notifications
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
]