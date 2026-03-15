"""
Bino bo'yicha filtrlash uchun admin mixinlar.

Superuser — barcha binolarni ko'radi.
building biriktirilgan user — faqat o'z binosini ko'radi.
"""


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


class BuildingFilteredFormMixin(BuildingFilterMixin):
    """
    Formfield'larni ham filtrlaydigan mixin (dropdown'larda faqat o'z binosi).
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        building_id = self.get_building_id(request)
        if building_id:
            from buildings.models import Building, Floor, Room
            if db_field.name == 'building':
                kwargs['queryset'] = Building.objects.filter(id=building_id)
            elif db_field.name == 'floor':
                kwargs['queryset'] = Floor.objects.filter(building_id=building_id)
            elif db_field.name == 'room':
                kwargs['queryset'] = Room.objects.filter(floor__building_id=building_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
