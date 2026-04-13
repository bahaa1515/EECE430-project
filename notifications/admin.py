from django.contrib import admin
from .models import Notification, NotificationRecipient


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'action', 'created_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['title', 'description']


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ['notification', 'user', 'is_read', 'read_at']
    list_filter = ['is_read']
    search_fields = ['notification__title', 'user__username', 'user__first_name', 'user__last_name']
