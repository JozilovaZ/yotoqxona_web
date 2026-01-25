from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Daily attendance
    path('', views.AttendanceDashboardView.as_view(), name='dashboard'),
    path('daily/', views.DailyAttendanceView.as_view(), name='daily'),
    path('mark/', views.MarkAttendanceView.as_view(), name='mark'),

    # History
    path('history/', views.AttendanceHistoryView.as_view(), name='history'),
    path('student/<int:student_pk>/', views.StudentAttendanceView.as_view(), name='student_history'),

    # Reports
    path('report/', views.AttendanceReportView.as_view(), name='report'),
    path('floor/<int:floor_pk>/', views.FloorAttendanceView.as_view(), name='floor'),
]