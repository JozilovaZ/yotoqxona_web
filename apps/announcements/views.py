from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Announcement
from .forms import AnnouncementForm
from accounts.view_mixins import BuildingStaffMixin


class AnnouncementListView(BuildingStaffMixin, ListView):
    """Barcha foydalanuvchilar uchun e'lonlar"""
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20

    def get_queryset(self):
        qs = Announcement.objects.filter(is_active=True).select_related('building', 'created_by')
        qs = qs.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        # Bino admini faqat o'z binosi va umumiy e'lonlarni ko'radi
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(Q(building_id=bid) | Q(building__isnull=True))

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Announcement.Category.choices
        ctx['selected_category'] = self.request.GET.get('category', '')
        return ctx


class AnnouncementCreateView(BuildingStaffMixin, CreateView):
    """Admin: yangi e'lon yaratish"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        bid = self.get_user_building_id()
        if bid:
            from buildings.models import Building
            form.fields['building'].queryset = Building.objects.filter(id=bid)
            form.fields['building'].initial = bid
        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Bino admini faqat o'z binosiga e'lon yaratadi
        bid = self.get_user_building_id()
        if bid:
            form.instance.building_id = bid
        messages.success(self.request, "E'lon muvaffaqiyatli yaratildi!")
        return super().form_valid(form)


class AnnouncementUpdateView(BuildingStaffMixin, UpdateView):
    """Admin: e'lonni tahrirlash"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')

    def get_queryset(self):
        qs = Announcement.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(building_id=bid)
        return qs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        bid = self.get_user_building_id()
        if bid:
            from buildings.models import Building
            form.fields['building'].queryset = Building.objects.filter(id=bid)
        return form

    def form_valid(self, form):
        messages.success(self.request, "E'lon yangilandi!")
        return super().form_valid(form)


class AnnouncementDeleteView(BuildingStaffMixin, DeleteView):
    """Admin: e'lonni o'chirish"""
    model = Announcement
    template_name = 'announcements/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcements:list')

    def get_queryset(self):
        qs = Announcement.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(building_id=bid)
        return qs

    def form_valid(self, form):
        messages.success(self.request, "E'lon o'chirildi!")
        return super().form_valid(form)
