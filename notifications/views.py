from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import NotificationForm
from .models import Notification, NotificationRecipient
from .services import create_notification


def _attach_breakdown(item):
    """Attach read/unread recipient lists — always excludes the creator."""
    creator_id = item.notification.created_by_id
    recipients = (
        NotificationRecipient.objects.filter(notification=item.notification)
        .select_related("user")
        .order_by("is_read", "user__first_name", "user__last_name")
    )
    # Never show the creator in either list
    recipients = [r for r in recipients if r.user_id != creator_id]
    item.read_recipients   = [r for r in recipients if r.is_read]
    item.unread_recipients = [r for r in recipients if not r.is_read]


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
        if not request.user.is_staff_role():
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

    # Recipients see their own NotificationRecipient rows.
    # Creators see a synthetic row so their own notifications stay visible.
    received = NotificationRecipient.objects.filter(user=request.user).select_related(
        "notification", "notification__created_by",
    )
    if query:
        received = received.filter(notification__title__icontains=query) | \
                   received.filter(notification__description__icontains=query)
    if filter_status == "Unread":
        received = received.filter(is_read=False)
    elif filter_status == "Read":
        received = received.filter(is_read=True)

    received = list(received.order_by("is_read", "-notification__created_at"))

    # Attach own-notification flag + breakdown to received items
    received_notif_ids = {item.notification_id for item in received}
    for item in received:
        item.is_own_notification = (item.notification.created_by_id == request.user.id)
        if item.is_own_notification:
            _attach_breakdown(item)

    # Add created-by-me notifications that aren't already in the received list
    own_notifs = Notification.objects.filter(created_by=request.user).select_related("created_by")
    if query:
        own_notifs = own_notifs.filter(title__icontains=query) | \
                     own_notifs.filter(description__icontains=query)
    own_notifs = own_notifs.order_by("-created_at")

    class _OwnItem:
        """Wraps a Notification so it looks like a NotificationRecipient to the template."""
        is_read = True          # creators have no read state
        is_own_notification = True

        def __init__(self, notification):
            self.notification = notification

    extra = []
    for notif in own_notifs:
        if notif.id not in received_notif_ids:
            item = _OwnItem(notif)
            _attach_breakdown(item)
            extra.append(item)

    notifications = received + extra
    # Re-sort: own notifications (created) first, then by date
    notifications.sort(key=lambda x: x.notification.created_at, reverse=True)

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
