"""
Bino bo'yicha filtrlash uchun admin mixinlar.

Superuser — barcha binolarni ko'radi.
building biriktirilgan user — faqat o'z binosini ko'radi va boshqaradi.
"""
from django.contrib import admin
from django.core.exceptions import PermissionDenied


class BuildingFilterMixin:
    """
    Admin queryset'ni user.building bo'yicha filtrlaydigan mixin.

    Subclasslar `building_filter_field` ni o'rnatishi kerak:
      - 'building' (to'g'ridan-to'g'ri)
      - 'room__floor__building'
      - 'student__room__floor__building'
      - 'floor__building'
      va h.k.
    """
    building_filter_field = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.building_id:
            if self.building_filter_field:
                qs = qs.filter(**{self.building_filter_field: request.user.building_id})
        return qs

    def get_building_id(self, request):
        if not request.user.is_superuser and request.user.building_id:
            return request.user.building_id
        return None

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and request.user.building_id:
            # Ob'ekt o'z queryset'imizda bormi tekshiramiz
            if not self.get_queryset(request).filter(pk=obj.pk).exists():
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and request.user.building_id:
            if not self.get_queryset(request).filter(pk=obj.pk).exists():
                return False
        return super().has_delete_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and request.user.building_id:
            if not self.get_queryset(request).filter(pk=obj.pk).exists():
                return False
        return super().has_view_permission(request, obj)


class BuildingFilteredFormMixin(BuildingFilterMixin):
    """
    Formfield'larni ham filtrlaydigan mixin (dropdown'larda faqat o'z binosi).
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        building_id = self.get_building_id(request)
        if building_id:
            from buildings.models import Building, Floor, Room
            from students.models import Student
            if db_field.name == 'building':
                kwargs['queryset'] = Building.objects.filter(id=building_id)
            elif db_field.name == 'floor':
                kwargs['queryset'] = Floor.objects.filter(building_id=building_id)
            elif db_field.name == 'room':
                kwargs['queryset'] = Room.objects.filter(floor__building_id=building_id)
            elif db_field.name == 'student':
                kwargs['queryset'] = Student.objects.filter(
                    room__floor__building_id=building_id
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Save qilishda bino tekshiruvi"""
        building_id = self.get_building_id(request)
        if building_id and self.building_filter_field:
            # Yangi ob'ekt yaratilganda yoki o'zgartirilganda
            # save qilib keyin queryset'da bormi tekshiramiz
            super().save_model(request, obj, form, change)
            if not self.get_queryset(request).filter(pk=obj.pk).exists():
                obj.delete()
                raise PermissionDenied("Siz faqat o'z binongizga tegishli ma'lumotlarni boshqara olasiz.")
        else:
            super().save_model(request, obj, form, change)
