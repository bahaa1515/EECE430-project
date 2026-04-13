from django.contrib import admin
from .models import MatchHighlight, MVP


@admin.register(MatchHighlight)
class MatchHighlightAdmin(admin.ModelAdmin):
    list_display = ["title", "session", "score", "created_at"]
    search_fields = ["title", "summary", "session__title"]
    list_filter = ["session"]


@admin.register(MVP)
class MVPAdmin(admin.ModelAdmin):
    list_display = ["player", "session", "points", "attack_success_rate", "blocks"]
    search_fields = ["player__name", "session__title"]
    list_filter = ["session"]
