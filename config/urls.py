"""
URL configuration for Yotoqxona Management System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# apps. prefiksini olib tashlaymiz
from buildings.views import DashboardView


def home_redirect(request):
    """Foydalanuvchi roliga qarab yo'naltirish"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.is_staff_member:
        return DashboardView.as_view()(request)
    # Talaba / Ariza beruvchi
    return redirect('applications:home')


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Dashboard (Bosh sahifa) - rolga qarab
    path('', login_required(home_redirect), name='dashboard'),

    # Barcha include'lardan 'apps.' prefiksini olib tashlaymiz
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('buildings/', include('buildings.urls', namespace='buildings')),
    path('students/', include('students.urls', namespace='students')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('applications/', include('applications.urls', namespace='applications')),
    path('announcements/', include('announcements.urls', namespace='announcements')),
]

# Media va Static fayllar (production da nginx serve qiladi)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)