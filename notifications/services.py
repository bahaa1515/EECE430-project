from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Notification, NotificationRecipient


def create_notification(
    *,
    title,
    description="",
    action=Notification.ACTION_VIEW,
    created_by=None,
    target_url="",
    recipients=None,
):
    recipient_queryset = recipients
    if recipient_queryset is None:
        recipient_queryset = get_user_model().objects.filter(is_active=True)

    with transaction.atomic():
        notification = Notification.objects.create(
            title=title,
            description=description,
            action=action,
            created_by=created_by,
            target_url=target_url,
        )
        NotificationRecipient.objects.bulk_create(
            [
                NotificationRecipient(notification=notification, user=user)
                for user in recipient_queryset
            ],
            ignore_conflicts=True,
        )
    return notification
