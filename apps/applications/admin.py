from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'student_id', 'room', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'student_id']
    readonly_fields = ['user', 'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
