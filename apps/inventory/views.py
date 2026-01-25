from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Count

from .models import InventoryCategory, InventoryItem, RoomInventory, InventoryLog
from .forms import CategoryForm, ItemForm, RoomInventoryForm
from apps.buildings.models import Room, Building


class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_categories'] = InventoryCategory.objects.count()
        context['total_items'] = InventoryItem.objects.count()
        context['total_room_items'] = RoomInventory.objects.aggregate(total=Sum('quantity'))['total'] or 0

        # Holat bo'yicha
        context['condition_stats'] = RoomInventory.objects.values('condition').annotate(
            count=Count('id')
        )

        # Kategoriya bo'yicha
        context['category_stats'] = InventoryCategory.objects.annotate(
            item_count=Count('items__room_items')
        ).order_by('-item_count')[:5]

        # Buzilgan jihozlar
        context['broken_items'] = RoomInventory.objects.filter(
            condition='broken'
        ).select_related('room', 'item')[:10]

        return context


class CategoryListView(LoginRequiredMixin, ListView):
    model = InventoryCategory
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = InventoryCategory
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Kategoriya yaratildi')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryCategory
    form_class = CategoryForm
    template_name = 'inventory/category_form.html'
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Kategoriya yangilandi')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = InventoryCategory
    template_name = 'inventory/category_confirm_delete.html'
    success_url = reverse_lazy('inventory:category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Kategoriya o\'chirildi')
        return super().form_valid(form)


class ItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = 'inventory/item_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        queryset = InventoryItem.objects.select_related('category')

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset.order_by('category', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = InventoryCategory.objects.all()
        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = InventoryItem
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('inventory:item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jihoz turi yaratildi')
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryItem
    form_class = ItemForm
    template_name = 'inventory/item_form.html'
    success_url = reverse_lazy('inventory:item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jihoz turi yangilandi')
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = 'inventory/item_confirm_delete.html'
    success_url = reverse_lazy('inventory:item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Jihoz turi o\'chirildi')
        return super().form_valid(form)


class RoomInventoryView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/room_inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = get_object_or_404(Room, pk=self.kwargs['room_pk'])
        context['room'] = room
        context['inventory'] = RoomInventory.objects.filter(room=room).select_related('item', 'item__category')
        context['total_value'] = sum(item.total_value for item in context['inventory'])
        return context


class RoomInventoryAddView(LoginRequiredMixin, CreateView):
    model = RoomInventory
    form_class = RoomInventoryForm
    template_name = 'inventory/room_inventory_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = get_object_or_404(Room, pk=self.kwargs['room_pk'])
        return context

    def form_valid(self, form):
        form.instance.room = get_object_or_404(Room, pk=self.kwargs['room_pk'])

        # Log yaratish
        result = super().form_valid(form)
        InventoryLog.objects.create(
            room_inventory=self.object,
            action='added',
            new_value=f'{self.object.quantity} ta',
            performed_by=self.request.user
        )

        messages.success(self.request, 'Jihoz qo\'shildi')
        return result

    def get_success_url(self):
        return reverse('inventory:room_inventory', kwargs={'room_pk': self.kwargs['room_pk']})


class RoomInventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = RoomInventory
    form_class = RoomInventoryForm
    template_name = 'inventory/room_inventory_form.html'

    def form_valid(self, form):
        old_instance = RoomInventory.objects.get(pk=self.object.pk)
        result = super().form_valid(form)

        # Agar holat o'zgargan bo'lsa
        if old_instance.condition != self.object.condition:
            InventoryLog.objects.create(
                room_inventory=self.object,
                action='condition',
                old_value=old_instance.get_condition_display(),
                new_value=self.object.get_condition_display(),
                performed_by=self.request.user
            )

        messages.success(self.request, 'Jihoz yangilandi')
        return result

    def get_success_url(self):
        return reverse('inventory:room_inventory', kwargs={'room_pk': self.object.room.pk})


class RoomInventoryDeleteView(LoginRequiredMixin, DeleteView):
    model = RoomInventory
    template_name = 'inventory/room_inventory_confirm_delete.html'

    def get_success_url(self):
        return reverse('inventory:room_inventory', kwargs={'room_pk': self.object.room.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Jihoz o\'chirildi')
        return super().form_valid(form)


class InventoryReportView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Bino bo'yicha statistika
        context['building_stats'] = []
        for building in Building.objects.filter(is_active=True):
            rooms = Room.objects.filter(floor__building=building)
            inventory = RoomInventory.objects.filter(room__in=rooms)
            total_value = sum(item.total_value for item in inventory)
            context['building_stats'].append({
                'building': building,
                'item_count': inventory.aggregate(total=Sum('quantity'))['total'] or 0,
                'total_value': total_value
            })

        # Umumiy qiymat
        all_inventory = RoomInventory.objects.all()
        context['grand_total'] = sum(item.total_value for item in all_inventory)

        return context