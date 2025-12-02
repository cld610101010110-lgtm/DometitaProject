# Context processor for notifications and messages
from notifications.models import Notification
from appointments.models import AppointmentMessage

def notification_context(request):
    if request.user.is_authenticated:
        # Unread notifications
        notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

        # Unread messages count
        unread_messages_count = AppointmentMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return {
            'recent_notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'unread_messages_count': unread_messages_count
        }
    return {
        'unread_notifications_count': 0,
        'unread_messages_count': 0
    }