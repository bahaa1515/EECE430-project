from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


@login_required
def dashboard_view(request):
    from attendance.models import Match
    from notifications.models import NotificationRecipient
    from players.models import Player

    now = timezone.now()
    recent_notifs = NotificationRecipient.objects.filter(user=request.user).select_related(
        "notification",
        "notification__created_by",
    ).order_by("is_read", "-notification__created_at")[:4]
    upcoming_matches = Match.objects.filter(
        date__gte=now,
        status=Match.STATUS_UPCOMING,
    ).order_by("date")[:4]
    dashboard_stats = {
        "active_players": Player.objects.filter(is_active=True).count(),
        "upcoming_matches": Match.objects.filter(
            date__gte=now,
            status=Match.STATUS_UPCOMING,
        ).count(),
        "needs_attention": Match.objects.filter(
            status__in=[Match.STATUS_CANCELLED, Match.STATUS_POSTPONED],
        ).count(),
        "pending_notifications": NotificationRecipient.objects.filter(
            user=request.user,
            is_read=False,
        ).count(),
    }
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "recent_notifs": recent_notifs,
            "upcoming_matches": upcoming_matches,
            "dashboard_stats": dashboard_stats,
            "active": "dashboard",
        },
    )
