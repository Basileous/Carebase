from .models import Appointment, Notification


def user_appointments(request):
    """Injects the current user's appointments and unread notification count into every template context."""
    if request.user.is_authenticated:
        try:
            appts = Appointment.objects.filter(
                patient__user=request.user
            ).select_related('doctor').order_by('-date')[:10]
            unread_count = Notification.objects.filter(
                patient__user=request.user, is_read=False
            ).count()
            return {'user_appointments': appts, 'unread_notifications': unread_count}
        except Exception:
            pass
    return {'user_appointments': [], 'unread_notifications': 0}
