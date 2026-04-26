from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import coach_required
from statistics_app.models import PlayerStat

from .forms import PlayerCreateForm, PlayerEditForm, SwapStarterForm
from .models import Player


@login_required
def players_list(request):
    starters = Player.objects.filter(
        player_type=Player.TYPE_STARTING,
        is_active=True,
    ).select_related("user")
    substitutes = Player.objects.filter(
        player_type=Player.TYPE_SUBSTITUTE,
        is_active=True,
    ).select_related("user")
    inactive_players = Player.objects.filter(is_active=False).select_related("user")

    return render(
        request,
        "players/players.html",
        {
            "starters": starters,
            "substitutes": substitutes,
            "inactive_players": inactive_players,
            "active": "players",
        },
    )


@login_required
def player_detail(request, player_id):
    player = get_object_or_404(Player.objects.select_related("user"), pk=player_id)
    stats = PlayerStat.objects.filter(player=player).order_by("-date")
    live_totals = stats.aggregate(
        matches=Count("id"),
        kills=Sum("kills"),
        blocks=Sum("blocks"),
        aces=Sum("aces"),
        mvp_awards=Count("id", filter=Q(mvp=True)),
    )
    attendance_summary = player.attendance_summary

    return render(
        request,
        "players/player_detail.html",
        {
            "player": player,
            "stats": stats[:10],
            "live_totals": live_totals,
            "attendance_summary": attendance_summary,
            "active": "players",
        },
    )


@coach_required
def player_add(request):
    form = PlayerCreateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        player = form.save()
        messages.success(request, f"{player.name} was added to the roster. They can log in with {player.user.email}.")
        return redirect("players")

    return render(
        request,
        "players/player_form.html",
        {
            "form": form,
            "page_title": "Add Player",
            "submit_label": "Add Player",
            "is_create": True,
            "active": "players",
        },
    )


@coach_required
def player_edit(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    form = PlayerEditForm(request.POST or None, request.FILES or None, instance=player)
    if request.method == "POST" and form.is_valid():
        updated_player = form.save()
        messages.success(request, f"{updated_player.name} was updated.")
        return redirect("players")

    return render(
        request,
        "players/player_form.html",
        {
            "form": form,
            "player": player,
            "page_title": "Edit Player",
            "submit_label": "Save Changes",
            "active": "players",
        },
    )


@coach_required
def player_deactivate(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    if request.method == "POST":
        player.is_active = False
        player.save(update_fields=["is_active"])
        messages.success(request, f"{player.name} was removed from the active roster.")
        return redirect("players")

    return render(
        request,
        "players/player_confirm_action.html",
        {
            "player": player,
            "action_title": "Deactivate Player",
            "action_text": "This will remove the player from the active roster while keeping their history and statistics.",
            "submit_label": "Deactivate Player",
            "active": "players",
        },
    )


@coach_required
def promote_player(request, player_id):
    player = get_object_or_404(Player, pk=player_id, is_active=True)
    if request.method == "POST":
        active_starters = Player.active_starters().exclude(pk=player.pk)
        if active_starters.count() >= Player.MAX_STARTERS:
            messages.error(
                request,
                f"Only {Player.MAX_STARTERS} starters are allowed. Demote or swap a current starter first.",
            )
            return redirect("players")
        player.player_type = Player.TYPE_STARTING
        player.save(update_fields=["player_type"])
        messages.success(request, f"{player.name} was promoted to the starting lineup.")
    return redirect("players")


@coach_required
def demote_player(request, player_id):
    player = get_object_or_404(Player, pk=player_id, is_active=True)
    if request.method == "POST":
        player.player_type = Player.TYPE_SUBSTITUTE
        player.save(update_fields=["player_type"])
        messages.success(request, f"{player.name} was moved to substitutes.")
    return redirect("players")


@coach_required
def swap_starter(request, player_id):
    starter = get_object_or_404(
        Player,
        pk=player_id,
        is_active=True,
        player_type=Player.TYPE_STARTING,
    )
    form = SwapStarterForm(request.POST or None, starter=starter)
    if request.method == "POST" and form.is_valid():
        replacement = form.cleaned_data["replacement"]
        with transaction.atomic():
            starter.player_type = Player.TYPE_SUBSTITUTE
            replacement.player_type = Player.TYPE_STARTING
            starter.save(update_fields=["player_type"])
            replacement.save(update_fields=["player_type"])
        messages.success(
            request,
            f"{replacement.name} is now starting and {starter.name} moved to substitutes.",
        )
        return redirect("players")

    return render(
        request,
        "players/player_swap.html",
        {
            "starter": starter,
            "form": form,
            "active": "players",
        },
    )
