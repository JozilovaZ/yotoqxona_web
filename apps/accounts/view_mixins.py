"""
Staff viewlar uchun bino bo'yicha filtrlash mixin.
Superuser — hamma narsani ko'radi.
building biriktirilgan user — faqat o'z binosini.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from buildings.models import Building, Floor, Room


class BuildingStaffMixin(LoginRequiredMixin):
    """
    Barcha staff viewlar uchun umumiy mixin.
    user.building bo'lsa, context'ga qo'shadi va filtrlash uchun helper beradi.
    """

    def get_user_building(self):
        user = self.request.user
        if not user.is_superuser and user.building_id:
            return user.building
        return None

    def get_user_building_id(self):
        user = self.request.user
        if not user.is_superuser and user.building_id:
            return user.building_id
        return None

    def filter_by_building(self, qs, field='floor__building'):
        """Queryset'ni bino bo'yicha filtrla"""
        bid = self.get_user_building_id()
        if bid:
            return qs.filter(**{field: bid})
        return qs

    def get_buildings_qs(self):
        """Ko'rishi mumkin bo'lgan binolar"""
        bid = self.get_user_building_id()
        if bid:
            return Building.objects.filter(id=bid)
        return Building.objects.filter(is_active=True)

    def get_floors_qs(self):
        bid = self.get_user_building_id()
        if bid:
            return Floor.objects.filter(building_id=bid, is_active=True)
        return Floor.objects.filter(is_active=True)

    def get_rooms_qs(self):
        bid = self.get_user_building_id()
        if bid:
            return Room.objects.filter(floor__building_id=bid, is_active=True)
        return Room.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_building'] = self.get_user_building()
        ctx['is_building_admin'] = self.get_user_building_id() is not None
        return ctx
