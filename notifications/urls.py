from django.urls import path
from . import views
urlpatterns = [
    path('', views.notifications_list, name='notifications'),
    path('<int:notification_id>/action/', views.notification_action, name='notification_action'),
]
