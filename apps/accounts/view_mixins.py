"""
Staff viewlar uchun bino bo'yicha filtrlash mixin.
Superuser (menejer) — hamma narsani ko'radi, faqat bino qo'sha oladi.
building biriktirilgan user (bino admin) — o'z binosini to'liq boshqaradi.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
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

    def can_manage(self):
        """
        Bino ichidagi resurslarni boshqara oladimi?
        Superuser — faqat ko'radi (binolardan tashqari).
        Bino admin — o'z binosini to'liq boshqaradi.
        """
        user = self.request.user
        if user.is_superuser:
            return False  # Menejer faqat ko'radi
        if user.building_id:
            return True   # Bino admini boshqaradi
        return False

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
        ctx['can_manage'] = self.can_manage()
        return ctx


class ManagePermissionMixin:
    """
    Create/Update/Delete viewlarga qo'shiladi.
    Superuser (menejer) bu viewlarga kira olmaydi — faqat bino admin.
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser:
            raise PermissionDenied("Siz menejer sifatida faqat ko'rish huquqiga egasiz. Boshqarish uchun bino adminiga murojaat qiling.")
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin:
    """
    Faqat superuser (menejer) kira oladi.
    Bino adminlari binolarni yaratish/o'chirish huquqiga ega emas.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Bu amal faqat bosh menejer uchun.")
        return super().dispatch(request, *args, **kwargs)
