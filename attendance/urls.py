from django.urls import path
from . import views
urlpatterns = [
    path('', views.attendance_view, name='attendance'),
    path('sessions/', views.sessions_calendar, name='sessions_calendar'),
    path('mark/<int:match_id>/', views.mark_attendance, name='mark_attendance'),
    path('coach/match/<int:match_id>/attendance/', views.update_match_attendance, name='update_match_attendance'),
    path('matches/add/', views.match_create, name='match_create'),
    path('matches/<int:match_id>/edit/', views.match_edit, name='match_edit'),
    path('matches/<int:match_id>/delete/', views.match_delete, name='match_delete'),
]
