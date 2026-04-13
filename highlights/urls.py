from django.urls import path
from . import views
urlpatterns = [
    path('', views.highlights_view, name='highlights'),
]
