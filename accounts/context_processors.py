# Create context processor for notifications
# Add this to accounts/context_processors.py
from notifications.models import Notification

def notification_context(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
        unread_count = notifications.count()
        return {
            'recent_notifications': notifications,
            'unread_count': unread_count
        }
    return {}