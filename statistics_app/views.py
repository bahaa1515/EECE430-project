from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import coach_required
from attendance.models import AttendanceRecord, Match
from players.models import Player

from .forms import PlayerStatForm, SessionStatForm
from .models import PlayerStat, SessionStat, TeamStat


@login_required
def statistics_view(request):
    now = timezone.now()
    stat = TeamStat.objects.first()

    computed_summary = {
        "active_players": Player.objects.filter(is_active=True).count(),
        "starting_players": Player.objects.filter(
            is_active=True,
            player_type=Player.TYPE_STARTING,
        ).count(),
        "substitutes": Player.objects.filter(
            is_active=True,
            player_type=Player.TYPE_SUBSTITUTE,
        ).count(),
        "completed_matches": Match.objects.filter(status=Match.STATUS_COMPLETED).count(),
        "upcoming_matches": Match.objects.filter(
            date__gte=now,
            status=Match.STATUS_UPCOMING,
        ).count(),
        "status_issues": Match.objects.filter(
            status__in=[Match.STATUS_CANCELLED, Match.STATUS_POSTPONED, Match.STATUS_PROBLEM],
        ).count(),
    }
    attendance_breakdown = AttendanceRecord.objects.aggregate(
        total=Count(
            "id",
            filter=Q(
                official_status__in=[
                    AttendanceRecord.OFFICIAL_PRESENT,
                    AttendanceRecord.OFFICIAL_ABSENT,
                    AttendanceRecord.OFFICIAL_LATE,
                ]
            ),
        ),
        attending=Count(
            "id",
            filter=Q(
                official_status__in=[
                    AttendanceRecord.OFFICIAL_PRESENT,
                    AttendanceRecord.OFFICIAL_LATE,
                ]
            ),
        ),
        not_attending=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_ABSENT)),
        pending=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_PENDING)),
        excused=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_EXCUSED)),
    )
    live_player_stats = PlayerStat.objects.values(
        "player__id",
        "player__name",
    ).annotate(
        matches=Count("id"),
        kills=Sum("kills"),
        blocks=Sum("blocks"),
        aces=Sum("aces"),
        mvp_awards=Count("id", filter=Q(mvp=True)),
    ).order_by("-kills", "-aces", "player__name")[:5]
    recent_session_stats = SessionStat.objects.select_related("match").order_by("-match__date", "-id")[:8]
    recent_match_logs = PlayerStat.objects.select_related("player").order_by("-date", "-id")[:12]

    return render(
        request,
        "statistics_app/statistics.html",
        {
            "stat": stat,
            "computed_summary": computed_summary,
            "attendance_breakdown": attendance_breakdown,
            "live_player_stats": live_player_stats,
            "recent_session_stats": recent_session_stats,
            "recent_match_logs": recent_match_logs,
            "active": "statistics",
        },
    )


@coach_required
def player_stat_create(request):
    initial = {}
    player_id = request.GET.get("player")
    if player_id:
        initial["player"] = Player.objects.filter(pk=player_id, is_active=True).first()

    form = PlayerStatForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        stat = form.save()
        messages.success(request, f"Match stats recorded for {stat.player.name}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/player_stat_form.html",
        {
            "form": form,
            "page_title": "Record Player Stats",
            "submit_label": "Save Player Stats",
            "active": "statistics",
        },
    )


@coach_required
def player_stat_edit(request, stat_id):
    stat = get_object_or_404(PlayerStat.objects.select_related("player"), pk=stat_id)
    form = PlayerStatForm(request.POST or None, instance=stat)
    if request.method == "POST" and form.is_valid():
        saved_stat = form.save()
        messages.success(request, f"Match stats updated for {saved_stat.player.name}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/player_stat_form.html",
        {
            "form": form,
            "stat": stat,
            "page_title": "Edit Player Stats",
            "submit_label": "Save Changes",
            "active": "statistics",
        },
    )


@coach_required
def player_stat_delete(request, stat_id):
    stat = get_object_or_404(PlayerStat.objects.select_related("player"), pk=stat_id)
    if request.method == "POST":
        player_name = stat.player.name
        stat.delete()
        messages.success(request, f"Match stats deleted for {player_name}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/player_stat_confirm_delete.html",
        {
            "stat": stat,
            "active": "statistics",
        },
    )


@coach_required
def session_stat_create(request):
    initial = {}
    match_id = request.GET.get("match")
    if match_id:
        match = Match.objects.filter(pk=match_id).first()
        if match is not None:
            existing_stat = SessionStat.objects.filter(match=match).first()
            if existing_stat is not None:
                messages.info(request, f"Session stats already exist for {match.title}.")
                return redirect("session_stat_edit", stat_id=existing_stat.id)
            initial["match"] = match

    form = SessionStatForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        stat = form.save()
        messages.success(request, f"Session stats saved for {stat.match.title}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/session_stat_form.html",
        {
            "form": form,
            "page_title": "Record Session Stats",
            "submit_label": "Save Session Stats",
            "active": "statistics",
        },
    )


@coach_required
def session_stat_edit(request, stat_id):
    stat = get_object_or_404(SessionStat.objects.select_related("match"), pk=stat_id)
    form = SessionStatForm(request.POST or None, instance=stat)
    if request.method == "POST" and form.is_valid():
        saved_stat = form.save()
        messages.success(request, f"Session stats updated for {saved_stat.match.title}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/session_stat_form.html",
        {
            "form": form,
            "stat": stat,
            "page_title": "Edit Session Stats",
            "submit_label": "Save Changes",
            "active": "statistics",
        },
    )


@coach_required
def session_stat_delete(request, stat_id):
    stat = get_object_or_404(SessionStat.objects.select_related("match"), pk=stat_id)
    if request.method == "POST":
        match_title = stat.match.title
        stat.delete()
        messages.success(request, f"Session stats deleted for {match_title}.")
        return redirect("statistics")

    return render(
        request,
        "statistics_app/session_stat_confirm_delete.html",
        {
            "stat": stat,
            "active": "statistics",
        },
    )
