from django.contrib import admin
from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['jersey_number', 'name', 'position', 'player_type', 'user', 'is_active']
    list_filter = ['player_type', 'position', 'is_active']
    search_fields = ['name', 'user__username', 'user__first_name', 'user__last_name']
