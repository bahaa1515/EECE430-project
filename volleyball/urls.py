from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('dashboard')),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('notifications/', include('notifications.urls')),
    path('attendance/', include('attendance.urls')),
    path('players/', include('players.urls')),
    path('statistics/', include('statistics_app.urls')),
    path('highlights/', include('highlights.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
