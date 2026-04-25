import json
from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from accounts.permissions import coach_required
from notifications.services import create_notification
from players.models import Player
from statistics_app.models import SessionStat

from .forms import HOME_VENUE, MatchForm
from .models import AttendanceRecord, Match


MATCH_STATUS_NOTIFICATIONS = {
    Match.STATUS_CANCELLED,
    Match.STATUS_POSTPONED,
}


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _build_querystring(params, exclude=None):
    exclude = set(exclude or [])
    filtered = {}
    for key, value in params.items():
        if key in exclude or value in ("", None):
            continue
        filtered[key] = value
    return urlencode(filtered)


def _week_start(value=None):
    if value:
        parsed = _parse_date(value)
        if parsed:
            today = parsed
        else:
            today = timezone.localdate()
    else:
        today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def _datetime_from_slot(day, hour):
    return timezone.make_aware(datetime.combine(day, time(hour=hour)))


def _apply_match_filters(params, queryset=None):
    if queryset is None:
        queryset = Match.objects.all()

    query = params.get("q", "").strip()
    location = params.get("location", "").strip()
    duration = params.get("duration", "").strip()
    date_from = params.get("date_from", "").strip()
    date_to = params.get("date_to", "").strip()
    match_type = params.get("match_type", "").strip()
    status = params.get("status", "").strip()

    if query:
        queryset = queryset.filter(title__icontains=query)
    if location:
        queryset = queryset.filter(location__iexact=location)
    if duration:
        try:
            queryset = queryset.filter(duration_hours=int(duration))
        except ValueError:
            duration = ""
    if match_type in dict(Match.TYPE_CHOICES):
        queryset = queryset.filter(match_type=match_type)
    else:
        match_type = ""
    if status in dict(Match.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    else:
        status = ""

    date_from_value = _parse_date(date_from)
    date_to_value = _parse_date(date_to)
    if date_from_value:
        queryset = queryset.filter(date__date__gte=date_from_value)
    else:
        date_from = ""
    if date_to_value:
        queryset = queryset.filter(date__date__lte=date_to_value)
    else:
        date_to = ""

    filters = {
        "q": query,
        "location": location,
        "duration": duration,
        "date_from": date_from,
        "date_to": date_to,
        "match_type": match_type,
        "status": status,
    }
    return queryset.order_by("date"), filters


def _notify_match_status_change(match, created=False, previous_status=None, actor=None):
    if match.status not in MATCH_STATUS_NOTIFICATIONS:
        return
    if not created and previous_status == match.status:
        return

    local_date = timezone.localtime(match.date)
    title = f"{match.match_type}: {match.title} is now {match.get_status_display()}"
    description = (
        f"{match.title} on {local_date.strftime('%A, %B %d at %I:%M %p')} "
        f"at {match.location} was marked as {match.get_status_display().lower()}."
    )
    create_notification(
        title=title,
        description=description,
        action="View",
        created_by=actor,
        target_url=f"{reverse('attendance')}?match={match.pk}",
        recipients=CustomUser.objects.filter(is_active=True),
    )


def _attendance_totals_for_user(user):
    records = AttendanceRecord.objects.filter(player=user).select_related("match")
    official_records = records.exclude(official_status=AttendanceRecord.OFFICIAL_PENDING)
    attended_records = official_records.filter(
        official_status__in=[
            AttendanceRecord.OFFICIAL_PRESENT,
            AttendanceRecord.OFFICIAL_LATE,
        ]
    )
    missed_records = official_records.filter(
        official_status=AttendanceRecord.OFFICIAL_ABSENT
    )
    excused_records = official_records.filter(
        official_status=AttendanceRecord.OFFICIAL_EXCUSED
    )

    matches_attended = attended_records.count()
    matches_missed = missed_records.count()
    matches_excused = excused_records.count()
    hours_attended = sum(record.match.duration_hours for record in attended_records)
    hours_missed = sum(record.match.duration_hours for record in missed_records)
    total_matches = (matches_attended + matches_missed) or 1
    total_hours = (hours_attended + hours_missed) or 1

    return {
        "matches_attended": matches_attended,
        "matches_missed": matches_missed,
        "matches_excused": matches_excused,
        "hours_attended": hours_attended,
        "hours_missed": hours_missed,
        "attended_pct": round(matches_attended / total_matches * 100),
        "missed_pct": round(matches_missed / total_matches * 100),
        "hours_attended_pct": round(hours_attended / total_hours * 100),
        "hours_missed_pct": round(hours_missed / total_hours * 100),
        "records": records,
    }


@login_required
def attendance_view(request):
    if request.user.is_coach():
        return coach_attendance(request)
    return player_attendance(request)


@login_required
def player_attendance(request):
    totals = _attendance_totals_for_user(request.user)
    records = totals["records"]
    records_by_match = {record.match_id: record for record in records}

    filter_type = request.GET.get("filter", "").strip()
    query = request.GET.get("q", "").strip()
    matches = Match.objects.select_related("coach").all().order_by("date")
    if query:
        matches = matches.filter(title__icontains=query)
    if filter_type in dict(Match.TYPE_CHOICES):
        matches = matches.filter(match_type=filter_type)
    else:
        filter_type = ""

    calendar_events = {}
    for match in Match.objects.select_related("coach").all():
        date_str = timezone.localtime(match.date).strftime("%Y-%m-%d")
        record = records_by_match.get(match.id)
        calendar_events.setdefault(date_str, []).append(
            {
                "id": match.id,
                "title": match.title,
                "type": match.match_type,
                "time": timezone.localtime(match.date).strftime("%A, %b %d | %I:%M %p"),
                "duration": match.duration_hours,
                "location": match.location,
                "coach": match.coach.get_full_name() if match.coach else "Coach",
                "response": (
                    record.response if record else AttendanceRecord.RESPONSE_NO_RESPONSE
                ),
                "official_status": (
                    record.official_status if record else AttendanceRecord.OFFICIAL_PENDING
                ),
                "match_status": match.status,
            }
        )

    paginator = Paginator(matches, 4)
    matches_page = paginator.get_page(request.GET.get("page", 1))
    match_data = [
        {"match": match, "record": records_by_match.get(match.id)}
        for match in matches_page
    ]

    return render(
        request,
        "attendance/player_attendance.html",
        {
            **totals,
            "match_data": match_data,
            "paginator": paginator,
            "matches_page": matches_page,
            "query": query,
            "filter_type": filter_type,
            "calendar_events": json.dumps(calendar_events),
            "querystring": _build_querystring(request.GET, exclude={"page"}),
            "active": "attendance",
        },
    )


@login_required
def sessions_calendar(request):
    week_start = _week_start(request.GET.get("week"))
    week_end = week_start + timedelta(days=7)
    previous_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    slot_hours = list(range(7, 23))
    week_start_dt = _datetime_from_slot(week_start, 0)
    week_end_dt = _datetime_from_slot(week_end, 0)

    sessions = list(
        Match.objects.select_related("coach")
        .filter(date__gte=week_start_dt, date__lt=week_end_dt)
        .order_by("date")
    )
    sessions_by_day = {}
    for session in sessions:
        local_start = timezone.localtime(session.date)
        local_end = local_start + timedelta(hours=session.duration_hours)
        sessions_by_day.setdefault(local_start.date(), []).append(
            {
                "session": session,
                "start": local_start,
                "end": local_end,
            }
        )

    calendar_days = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        day_sessions = sessions_by_day.get(day, [])
        slots = []
        for hour in slot_hours:
            slot_start = _datetime_from_slot(day, hour)
            slot_end = slot_start + timedelta(hours=1)
            slot_sessions = [
                item
                for item in day_sessions
                if item["start"] < slot_end and item["end"] > slot_start
            ]
            slots.append(
                {
                    "hour": hour,
                    "label": f"{hour:02d}:00",
                    "sessions": slot_sessions,
                }
            )
        calendar_days.append(
            {
                "date": day,
                "sessions": day_sessions,
                "slots": slots,
            }
        )
    calendar_rows = []
    for hour in slot_hours:
        row_slots = []
        for day in calendar_days:
            row_slots.append(
                next(slot for slot in day["slots"] if slot["hour"] == hour)
            )
        calendar_rows.append(
            {
                "hour": hour,
                "label": f"{hour:02d}:00",
                "slots": row_slots,
            }
        )

    upcoming_sessions = Match.objects.exclude(status=Match.STATUS_CANCELLED).filter(
        date__gte=timezone.now(),
    ).order_by("date")[:10]

    return render(
        request,
        "attendance/sessions_calendar.html",
        {
            "calendar_days": calendar_days,
            "calendar_rows": calendar_rows,
            "week_start": week_start,
            "week_end": week_end - timedelta(days=1),
            "previous_week": previous_week,
            "next_week": next_week,
            "upcoming_sessions": upcoming_sessions,
            "home_venue": HOME_VENUE,
            "active": "sessions",
        },
    )


@coach_required
def coach_attendance(request):
    matches, filters = _apply_match_filters(
        request.GET,
        Match.objects.select_related("coach", "session_stat"),
    )
    paginator = Paginator(matches, 6)
    matches_page = paginator.get_page(request.GET.get("page", 1))

    selected_match = None
    selected_match_id = request.GET.get("match")
    managed_request = request.GET.get("manage") == "1"
    if selected_match_id:
        selected_match = matches.filter(pk=selected_match_id).first()
    if selected_match is None:
        selected_match = next(iter(matches_page.object_list), None)
    if managed_request and selected_match:
        messages.info(
            request,
            f"Now managing attendance for {selected_match.title}.",
        )
    can_edit_official_attendance = (
        selected_match is not None and selected_match.status == Match.STATUS_COMPLETED
    )

    match_counts = AttendanceRecord.objects.filter(
        match_id__in=[match.id for match in matches_page.object_list]
    ).values("match_id").annotate(
        present=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_PRESENT)),
        absent=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_ABSENT)),
        late=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_LATE)),
        excused=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_EXCUSED)),
        pending_review=Count(
            "id",
            filter=Q(official_status=AttendanceRecord.OFFICIAL_PENDING),
        ),
    )
    count_map = {row["match_id"]: row for row in match_counts}
    session_stat_map = {
        session_stat.match_id: session_stat.id
        for session_stat in SessionStat.objects.filter(
            match_id__in=[match.id for match in matches_page.object_list]
        )
    }
    match_rows = []
    for match in matches_page:
        row = count_map.get(match.id, {})
        match_rows.append(
            {
                "match": match,
                "present": row.get("present", 0),
                "absent": row.get("absent", 0),
                "late": row.get("late", 0),
                "excused": row.get("excused", 0),
                "pending_review": row.get("pending_review", 0),
                "session_stat_id": session_stat_map.get(match.id),
            }
        )

    students = list(
        CustomUser.objects.filter(
            role=CustomUser.ROLE_STUDENT,
            is_active=True,
        ).order_by("first_name", "last_name", "username")
    )
    linked_players = {
        player.user_id: player
        for player in Player.objects.filter(
            user_id__in=[user.id for user in students]
        ).select_related("user")
    }
    selected_records = {}
    if selected_match:
        selected_records = {
            record.player_id: record
            for record in AttendanceRecord.objects.filter(
                match=selected_match,
                player__in=students,
            )
        }

    aggregate_rows = AttendanceRecord.objects.filter(player__in=students).values("player_id").annotate(
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
        not_attending=Count(
            "id",
            filter=Q(official_status=AttendanceRecord.OFFICIAL_ABSENT),
        ),
        pending=Count(
            "id",
            filter=Q(official_status=AttendanceRecord.OFFICIAL_PENDING),
        ),
        excused=Count(
            "id",
            filter=Q(official_status=AttendanceRecord.OFFICIAL_EXCUSED),
        ),
    )
    aggregate_map = {row["player_id"]: row for row in aggregate_rows}

    player_rows = []
    for student in students:
        summary = aggregate_map.get(
            student.id,
            {
                "total": 0,
                "attending": 0,
                "not_attending": 0,
                "pending": 0,
                "excused": 0,
            },
        )
        total = summary["total"]
        attendance_pct = round(summary["attending"] / total * 100) if total else None
        player_rows.append(
            {
                "user": student,
                "linked_player": linked_players.get(student.id),
                "response": (
                    selected_records.get(student.id).response
                    if selected_match and student.id in selected_records
                    else AttendanceRecord.RESPONSE_NO_RESPONSE
                ),
                "official_status": (
                    selected_records.get(student.id).official_status
                    if selected_match and student.id in selected_records
                    else AttendanceRecord.OFFICIAL_PENDING
                ),
                "summary": summary,
                "attendance_pct": attendance_pct,
            }
        )

    attendance_totals = AttendanceRecord.objects.aggregate(
        total=Count("id"),
        responded=Count(
            "id",
            filter=Q(
                response__in=[
                    AttendanceRecord.RESPONSE_AVAILABLE,
                    AttendanceRecord.RESPONSE_UNAVAILABLE,
                ]
            ),
        ),
    )
    response_rate = (
        round(attendance_totals["responded"] / attendance_totals["total"] * 100)
        if attendance_totals["total"]
        else 0
    )
    summary_cards = {
        "total_matches": Match.objects.count(),
        "upcoming_matches": Match.objects.filter(
            date__gte=timezone.now(),
            status=Match.STATUS_UPCOMING,
        ).count(),
        "completed_matches": Match.objects.filter(status=Match.STATUS_COMPLETED).count(),
        "response_rate": response_rate,
    }

    return render(
        request,
        "attendance/coach_attendance.html",
        {
            "summary_cards": summary_cards,
            "match_rows": match_rows,
            "matches_page": matches_page,
            "paginator": paginator,
            "filters": filters,
            "querystring": _build_querystring(request.GET, exclude={"page"}),
            "selected_match": selected_match,
            "can_edit_official_attendance": can_edit_official_attendance,
            "player_rows": player_rows,
            "location_choices": Match.objects.order_by("location").values_list("location", flat=True).distinct(),
            "duration_choices": Match.objects.order_by("duration_hours").values_list("duration_hours", flat=True).distinct(),
            "active": "attendance",
        },
    )


@login_required
def mark_attendance(request, match_id):
    if request.method != "POST":
        return redirect("attendance")

    match = get_object_or_404(Match, pk=match_id)
    response = request.POST.get("response") or request.POST.get("status")
    next_url = request.POST.get("next") or reverse("attendance")

    if request.user.is_coach():
        messages.error(request, "Coach attendance is managed from the team attendance page.")
        return redirect(next_url)

    valid_responses = {choice for choice, _ in AttendanceRecord.RESPONSE_CHOICES}
    if response not in valid_responses:
        messages.error(request, "Please choose a valid availability response.")
        return redirect(next_url)

    if match.status in {Match.STATUS_CANCELLED, Match.STATUS_COMPLETED}:
        messages.error(request, "Responses can no longer be changed for this session.")
        return redirect(next_url)

    if match.confirmation_closes and timezone.now() > match.confirmation_closes:
        messages.error(request, "Availability confirmation has already closed.")
        return redirect(next_url)

    record, _ = AttendanceRecord.objects.get_or_create(match=match, player=request.user)
    record.response = response
    record.save(update_fields=["response"])
    messages.success(request, "Your availability response was updated.")
    return redirect(next_url)


@coach_required
def update_match_attendance(request, match_id):
    if request.method != "POST":
        return redirect("attendance")

    match = get_object_or_404(Match, pk=match_id)
    if match.status != Match.STATUS_COMPLETED:
        messages.error(
            request,
            "Official attendance can only be recorded after the session is marked Completed.",
        )
        next_url = request.POST.get("next") or f"{reverse('attendance')}?match={match.pk}"
        return redirect(next_url)

    students = list(
        CustomUser.objects.filter(
            role=CustomUser.ROLE_STUDENT,
            is_active=True,
        )
    )
    valid_official_statuses = {
        choice for choice, _ in AttendanceRecord.OFFICIAL_STATUS_CHOICES
    }
    next_url = request.POST.get("next") or f"{reverse('attendance')}?match={match.pk}"

    with transaction.atomic():
        existing_records = {
            record.player_id: record
            for record in AttendanceRecord.objects.filter(match=match, player__in=students)
        }
        for student in students:
            official_status = request.POST.get(
                f"player_{student.id}",
                AttendanceRecord.OFFICIAL_PENDING,
            )
            if official_status not in valid_official_statuses:
                official_status = AttendanceRecord.OFFICIAL_PENDING

            record = existing_records.get(student.id)
            if record:
                if record.official_status != official_status:
                    record.official_status = official_status
                    record.save(update_fields=["official_status"])
            else:
                AttendanceRecord.objects.create(
                    match=match,
                    player=student,
                    official_status=official_status,
                )

    messages.success(request, f"Official attendance updated for {match.title}.")
    return redirect(next_url)


@coach_required
def match_create(request):
    initial = {"location": HOME_VENUE}
    requested_date = request.GET.get("date")
    if requested_date:
        initial["date"] = requested_date

    form = MatchForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        match = form.save(commit=False)
        match.coach = request.user
        match.save()
        _notify_match_status_change(match, created=True, actor=request.user)
        messages.success(request, f"{match.match_type} created successfully.")
        return redirect("sessions_calendar")

    return render(
        request,
        "attendance/match_form.html",
        {
            "form": form,
            "page_title": "Create Match / Practice",
            "submit_label": "Create Session",
            "home_venue": HOME_VENUE,
            "active": "sessions",
        },
    )


@coach_required
def match_edit(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    previous_status = match.status
    form = MatchForm(request.POST or None, instance=match)
    if request.method == "POST" and form.is_valid():
        updated_match = form.save()
        if not updated_match.coach_id:
            updated_match.coach = request.user
            updated_match.save(update_fields=["coach"])
        _notify_match_status_change(
            updated_match,
            previous_status=previous_status,
            actor=request.user,
        )
        messages.success(request, f"{updated_match.title} updated successfully.")
        return redirect("sessions_calendar")

    return render(
        request,
        "attendance/match_form.html",
        {
            "form": form,
            "match": match,
            "page_title": "Edit Match / Practice",
            "submit_label": "Save Changes",
            "home_venue": HOME_VENUE,
            "active": "sessions",
        },
    )


@coach_required
def match_delete(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == "POST":
        title = match.title
        match.delete()
        messages.success(request, f"{title} was deleted.")
        return redirect("sessions_calendar")

    return render(
        request,
        "attendance/match_confirm_delete.html",
        {
            "match": match,
            "active": "sessions",
        },
    )
