from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Announcement
from .forms import AnnouncementForm


class AnnouncementListView(LoginRequiredMixin, ListView):
    """Barcha foydalanuvchilar uchun e'lonlar"""
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20

    def get_queryset(self):
        qs = Announcement.objects.filter(is_active=True).select_related('building', 'created_by')
        # Muddati o'tganlarni chiqarish
        qs = qs.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Announcement.Category.choices
        ctx['selected_category'] = self.request.GET.get('category', '')
        return ctx


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Admin: yangi e'lon yaratish"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "E'lon muvaffaqiyatli yaratildi!")
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, UpdateView):
    """Admin: e'lonni tahrirlash"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')

    def form_valid(self, form):
        messages.success(self.request, "E'lon yangilandi!")
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, DeleteView):
    """Admin: e'lonni o'chirish"""
    model = Announcement
    template_name = 'announcements/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcements:list')

    def form_valid(self, form):
        messages.success(self.request, "E'lon o'chirildi!")
        return super().form_valid(form)
