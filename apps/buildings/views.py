from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, Exists, OuterRef
from django.utils import timezone

from .models import Building, Floor, Room
from .forms import BuildingForm, FloorForm, RoomForm
from students.models import Student
from finance.models import Payment, Invoice
from attendance.models import Attendance


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'buildings/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Umumiy statistika
        context['total_buildings'] = Building.objects.filter(is_active=True).count()
        context['total_rooms'] = Room.objects.filter(is_active=True).count()
        context['total_students'] = Student.objects.filter(is_active=True).count()

        # Xonalar statistikasi
        total_capacity = Room.objects.filter(is_active=True).aggregate(
            total=Sum('capacity')
        )['total'] or 0
        context['total_capacity'] = total_capacity
        context['occupied_beds'] = context['total_students']
        context['free_beds'] = max(0, total_capacity - context['total_students'])
        context['occupancy_rate'] = round(
            (context['total_students'] / total_capacity * 100) if total_capacity > 0 else 0, 1
        )

        # Bo'sh xonalar
        context['empty_rooms'] = Room.objects.filter(is_active=True, status='available').count()
        context['full_rooms'] = Room.objects.filter(is_active=True, status='full').count()
        context['partial_rooms'] = Room.objects.filter(is_active=True, status='partial').count()

        # Moliya - bu oy
        context['total_collected_month'] = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Moliya - bugun
        context['total_collected_today'] = Payment.objects.filter(
            payment_date__date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Kutilayotgan to'lovlar
        context['pending_amount'] = Invoice.objects.filter(
            status__in=['pending', 'partial', 'overdue']
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Qarzdorlar
        context['debtors_count'] = Student.objects.filter(
            is_active=True
        ).annotate(
            total_invoiced=Sum('invoices__amount'),
            total_paid=Sum('payments__amount', filter=Q(payments__status='completed'))
        ).filter(
            total_invoiced__gt=0
        ).exclude(
            total_paid__gte=F('total_invoiced')
        ).count()

        # Davomat
        today_att = Attendance.objects.filter(date=today)
        context['today_present'] = today_att.filter(status='present').count()
        context['today_absent'] = today_att.filter(status='absent').count()
        context['today_attendance'] = context['today_present']
        context['attendance_rate'] = round(
            (context['today_present'] / context['total_students'] * 100)
            if context['total_students'] > 0 else 0, 1
        )

        # Oxirgi talabalar
        context['recent_students'] = Student.objects.filter(
            is_active=True
        ).select_related('room', 'room__floor', 'room__floor__building').order_by('-created_at')[:8]

        # Oxirgi to'lovlar
        context['recent_payments'] = Payment.objects.filter(
            status='completed'
        ).select_related('student').order_by('-payment_date')[:6]

        # Binolar bandlik ma'lumoti
        buildings = Building.objects.filter(is_active=True)
        buildings_data = []
        for b in buildings:
            cap = Room.objects.filter(floor__building=b, is_active=True).aggregate(
                total=Sum('capacity'))['total'] or 0
            occ = Student.objects.filter(room__floor__building=b, is_active=True).count()
            rate = round((occ / cap * 100) if cap > 0 else 0)
            buildings_data.append({
                'building': b,
                'capacity': cap,
                'occupied': occ,
                'free': max(0, cap - occ),
                'rate': rate,
            })
        context['buildings_data'] = buildings_data

        # Xonalar holati
        context['rooms_by_status'] = Room.objects.filter(is_active=True).values('status').annotate(
            count=Count('id')
        )

        return context


# Building Views
class BuildingListView(LoginRequiredMixin, ListView):
    model = Building
    template_name = 'buildings/building_list.html'
    context_object_name = 'buildings'

    def get_queryset(self):
        return Building.objects.filter(is_active=True).prefetch_related('floors', 'floors__rooms')


class BuildingDetailView(LoginRequiredMixin, DetailView):
    model = Building
    template_name = 'buildings/building_detail.html'
    context_object_name = 'building'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['floors'] = self.object.floors.filter(is_active=True).prefetch_related('rooms')
        return context

class BuildingCreateView(LoginRequiredMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('buildings:building_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bino muvaffaqiyatli yaratildi')
        return super().form_valid(form)


class BuildingUpdateView(LoginRequiredMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('buildings:building_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bino muvaffaqiyatli yangilandi')
        return super().form_valid(form)


class BuildingDeleteView(LoginRequiredMixin, DeleteView):
    model = Building
    template_name = 'buildings/building_confirm_delete.html'
    success_url = reverse_lazy('buildings:building_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bino o\'chirildi')
        return super().form_valid(form)


# Floor Views
class FloorListView(LoginRequiredMixin, ListView):
    model = Floor
    template_name = 'buildings/floor_list.html'
    context_object_name = 'floors'

    def get_queryset(self):
        self.building = get_object_or_404(Building, pk=self.kwargs['building_pk'])
        return Floor.objects.filter(building=self.building, is_active=True).prefetch_related('rooms')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['building'] = self.building
        return context


class FloorCreateView(LoginRequiredMixin, CreateView):
    model = Floor
    form_class = FloorForm
    template_name = 'buildings/floor_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['building'] = get_object_or_404(Building, pk=self.kwargs['building_pk'])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['building'] = get_object_or_404(Building, pk=self.kwargs['building_pk'])
        return context

    def form_valid(self, form):
        form.instance.building = get_object_or_404(Building, pk=self.kwargs['building_pk'])
        messages.success(self.request, 'Etaj muvaffaqiyatli qo\'shildi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.kwargs['building_pk']})


class FloorUpdateView(LoginRequiredMixin, UpdateView):
    model = Floor
    form_class = FloorForm
    template_name = 'buildings/floor_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Etaj muvaffaqiyatli yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.building.pk})


class FloorDeleteView(LoginRequiredMixin, DeleteView):
    model = Floor
    template_name = 'buildings/floor_confirm_delete.html'

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.building.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Etaj o\'chirildi')
        return super().form_valid(form)


# Room Views
class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'buildings/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 20

    def get_queryset(self):
        queryset = Room.objects.filter(is_active=True).select_related(
            'floor', 'floor__building'
        ).prefetch_related('students')

        # Filtrlash
        building = self.request.GET.get('building')
        floor = self.request.GET.get('floor')
        status = self.request.GET.get('status')
        room_type = self.request.GET.get('type')

        if building:
            queryset = queryset.filter(floor__building_id=building)
        if floor:
            queryset = queryset.filter(floor_id=floor)
        if status:
            queryset = queryset.filter(status=status)
        if room_type:
            queryset = queryset.filter(room_type=room_type)

        return queryset.order_by('floor__building', 'floor__number', 'number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.filter(is_active=True)
        context['room_statuses'] = Room.RoomStatus.choices
        context['room_types'] = Room.RoomType.choices
        return context


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = 'buildings/room_detail.html'
    context_object_name = 'room'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()

        # Talabalarni joriy oydagi to'lov holati bilan birga olish
        context['students'] = Student.objects.filter(
            room=self.object,
            is_active=True
        ).annotate(
            has_paid=Exists(
                Payment.objects.filter(
                    student=OuterRef('pk'),
                    payment_date__year=today.year,
                    payment_date__month=today.month,
                    status='completed'
                )
            )
        )

        context['inventory'] = self.object.inventory.all().select_related('item', 'item__category')
        return context


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'buildings/room_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['floor'] = get_object_or_404(Floor, pk=self.kwargs['floor_pk'])
        return context

    def form_valid(self, form):
        form.instance.floor = get_object_or_404(Floor, pk=self.kwargs['floor_pk'])
        messages.success(self.request, 'Xona muvaffaqiyatli qo\'shildi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.floor.building.pk})


class RoomUpdateView(LoginRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'buildings/room_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Xona muvaffaqiyatli yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:room_detail', kwargs={'pk': self.object.pk})


class RoomDeleteView(LoginRequiredMixin, DeleteView):
    model = Room
    template_name = 'buildings/room_confirm_delete.html'

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.floor.building.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Xona o\'chirildi')
        return super().form_valid(form)


# API Views
@login_required
def get_floors_api(request, building_id):
    floors = Floor.objects.filter(building_id=building_id, is_active=True).values('id', 'number')
    return JsonResponse(list(floors), safe=False)


@login_required
def get_rooms_api(request, floor_id):
    rooms = Room.objects.filter(floor_id=floor_id, is_active=True).values(
        'id', 'number', 'capacity', 'status'
    )
    return JsonResponse(list(rooms), safe=False)