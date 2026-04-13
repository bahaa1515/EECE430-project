from django.urls import path
from . import views
urlpatterns = [
    path('', views.statistics_view, name='statistics'),
    path('logs/add/', views.player_stat_create, name='player_stat_create'),
    path('logs/<int:stat_id>/edit/', views.player_stat_edit, name='player_stat_edit'),
    path('logs/<int:stat_id>/delete/', views.player_stat_delete, name='player_stat_delete'),
]
