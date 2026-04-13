from django.contrib import admin
from .models import Match, AttendanceRecord


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['title', 'match_type', 'status', 'date', 'location', 'duration_hours']
    list_filter = ['match_type', 'status', 'location']
    search_fields = ['title', 'location']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['match', 'player', 'response', 'official_status']
    list_filter = ['response', 'official_status']
    search_fields = ['match__title', 'player__username', 'player__first_name', 'player__last_name']
