from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification

@login_required
def notification_list(request):
    """List all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Separate read and unread
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)
    
    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'title': 'Notifications'
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_as_read(request, pk):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')

@login_required
def mark_all_as_read(request):
    """Mark all notifications as read for the current user"""
    from django.utils import timezone
    
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    notifications.update(is_read=True, read_at=timezone.now())
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')

@login_required
def delete_notification(request, pk):
    """Delete a notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    
    messages.success(request, 'Notification deleted.')
    return redirect('notification_list')