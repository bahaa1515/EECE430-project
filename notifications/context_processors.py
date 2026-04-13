from .models import NotificationRecipient


def notification_context(request):
    if not request.user.is_authenticated:
        return {"navbar_unread_count": 0}

    unread_count = NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False,
    ).count()
    return {"navbar_unread_count": unread_count}
