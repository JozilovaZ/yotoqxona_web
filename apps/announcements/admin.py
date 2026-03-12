from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'priority', 'building', 'is_active', 'created_at']
    list_filter = ['category', 'priority', 'is_active', 'building']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
