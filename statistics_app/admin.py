from django.contrib import admin
from .models import TeamStat, PlayerStat


@admin.register(TeamStat)
class TeamStatAdmin(admin.ModelAdmin):
    list_display = ['season', 'home_played', 'home_wins', 'away_played', 'away_wins']


@admin.register(PlayerStat)
class PlayerStatAdmin(admin.ModelAdmin):
    list_display = ['player', 'date', 'opponent', 'kills', 'blocks', 'aces', 'mvp']
    list_filter = ['mvp', 'date']
    search_fields = ['player__name', 'opponent']
