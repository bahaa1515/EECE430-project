from django.urls import path
from . import views
urlpatterns = [
    path('', views.players_list, name='players'),
    path('add/', views.player_add, name='player_add'),
    path('<int:player_id>/', views.player_detail, name='player_detail'),
    path('<int:player_id>/edit/', views.player_edit, name='player_edit'),
    path('<int:player_id>/deactivate/', views.player_deactivate, name='player_deactivate'),
    path('<int:player_id>/promote/', views.promote_player, name='promote_player'),
    path('<int:player_id>/demote/', views.demote_player, name='demote_player'),
    path('<int:player_id>/swap/', views.swap_starter, name='swap_starter'),
]
