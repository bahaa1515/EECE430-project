from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import NotificationForm
from .models import NotificationRecipient
from .services import create_notification


def _build_querystring(query, filter_status):
    params = {}
    if query:
        params["q"] = query
    if filter_status:
        params["filter"] = filter_status
    return urlencode(params)


@login_required
def notifications_list(request):
    query = request.GET.get("q", "").strip()
    filter_status = request.GET.get("filter", "")
    show_add = request.GET.get("add", "")

    form = NotificationForm()
    if request.method == "POST":
        if not request.user.is_coach():
            raise PermissionDenied

        form = NotificationForm(request.POST)
        show_add = "1"
        if form.is_valid():
            create_notification(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                action=form.cleaned_data["action"],
                created_by=request.user,
                target_url=reverse("notifications"),
            )
            messages.success(request, "Notification posted for the team.")
            return redirect("notifications")

    notifications = NotificationRecipient.objects.filter(user=request.user).select_related(
        "notification",
        "notification__created_by",
    )
    if query:
        notifications = notifications.filter(
            notification__title__icontains=query,
        ) | notifications.filter(
            notification__description__icontains=query,
        )
    if filter_status == "Unread":
        notifications = notifications.filter(is_read=False)
    elif filter_status == "Read":
        notifications = notifications.filter(is_read=True)

    notifications = notifications.order_by("is_read", "-notification__created_at")
    paginator = Paginator(notifications, 6)
    notifications_page = paginator.get_page(request.GET.get("page", 1))

    return render(
        request,
        "notifications/notifications.html",
        {
            "notifications": notifications_page,
            "paginator": paginator,
            "query": query,
            "filter_status": filter_status,
            "show_add": show_add,
            "form": form,
            "querystring": _build_querystring(query, filter_status),
            "active": "notifications",
        },
    )


@login_required
def notification_action(request, notification_id):
    if request.method != "POST":
        return redirect("notifications")

    recipient = get_object_or_404(
        NotificationRecipient,
        notification_id=notification_id,
        user=request.user,
    )
    action = request.POST.get("action", "read")

    if action == "mark_unread":
        recipient.is_read = False
        recipient.read_at = None
        recipient.save(update_fields=["is_read", "read_at"])
        return redirect("notifications")

    recipient.is_read = True
    recipient.read_at = timezone.now()
    recipient.save(update_fields=["is_read", "read_at"])

    if action == "open" and recipient.notification.target_url:
        return redirect(recipient.notification.target_url)
    return redirect("notifications")
