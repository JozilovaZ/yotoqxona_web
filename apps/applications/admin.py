from django.contrib import admin
from django.utils.html import format_html
from .models import Application, CarouselImage


@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px;"/>', obj.image.url)
        return '-'
    image_preview.short_description = 'Rasm'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'student_id', 'room', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'student_id']
    readonly_fields = ['user', 'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
