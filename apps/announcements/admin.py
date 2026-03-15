from django.contrib import admin
from .models import Announcement
from accounts.admin_mixins import BuildingFilteredFormMixin


@admin.register(Announcement)
class AnnouncementAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'building'

    list_display = ['title', 'category', 'priority', 'building', 'is_active', 'created_at']
    list_filter = ['category', 'priority', 'is_active', 'building']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.building_id:
            # Bino admin o'z binosiga tegishli + umumiy (building=NULL) e'lonlarni ko'radi
            qs = qs.filter(
                building_id__in=[request.user.building_id, None]
            )
        return qs

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        # Bino admini faqat o'z binosi uchun e'lon yaratsin
        if not request.user.is_superuser and request.user.building_id and not obj.building_id:
            obj.building = request.user.building
        super().save_model(request, obj, form, change)
