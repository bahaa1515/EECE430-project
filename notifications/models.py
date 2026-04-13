from django.db import models
from django.utils import timezone


class Notification(models.Model):
    ACTION_VIEW = 'View'
    ACTION_CONFIRM = 'Confirm'
    ACTION_CHOICES = [(ACTION_VIEW,'View'), (ACTION_CONFIRM,'Confirm')]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default=ACTION_VIEW)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    target_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="notification_recipients",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["is_read", "-notification__created_at"]
        unique_together = ["notification", "user"]

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
