"""
URL configuration for Yotoqxona Management System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

# apps. prefiksini olib tashlaymiz
from buildings.views import DashboardView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Dashboard (Bosh sahifa)
    path('', login_required(DashboardView.as_view()), name='dashboard'),

    # Barcha include'lardan 'apps.' prefiksini olib tashlaymiz
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('buildings/', include('buildings.urls', namespace='buildings')),
    path('students/', include('students.urls', namespace='students')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
]

# Media va Static fayllar
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # STATICFILES_DIRS[0] o'rniga settings.STATIC_ROOT dan foydalanish xavfsizroq
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)