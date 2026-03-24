from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, Exists, OuterRef, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from itertools import groupby

from .models import Building, Floor, Room
from .forms import BuildingForm, FloorForm, RoomForm
from students.models import Student
from finance.models import Payment, Invoice
from attendance.models import Attendance
from accounts.view_mixins import BuildingStaffMixin, ManagePermissionMixin, SuperuserRequiredMixin


class DashboardView(BuildingStaffMixin, TemplateView):
    template_name = 'buildings/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        user = self.request.user

        # Bino filtr — admin faqat o'z binosini ko'radi
        bld_filter = {}
        room_bld_filter = {}
        student_bld_filter = {}
        if not user.is_superuser and user.building_id:
            bld_filter = {'id': user.building_id}
            room_bld_filter = {'floor__building_id': user.building_id}
            student_bld_filter = {'room__floor__building_id': user.building_id}
            context['user_building'] = user.building

        # Umumiy statistika
        context['total_buildings'] = Building.objects.filter(is_active=True, **bld_filter).count()
        rooms_qs = Room.objects.filter(is_active=True, **room_bld_filter)
        students_qs = Student.objects.filter(is_active=True, **student_bld_filter)
        context['total_rooms'] = rooms_qs.count()
        context['total_students'] = students_qs.count()

        # Xonalar statistikasi
        total_capacity = rooms_qs.aggregate(total=Sum('capacity'))['total'] or 0
        context['total_capacity'] = total_capacity
        context['occupied_beds'] = context['total_students']
        context['free_beds'] = max(0, total_capacity - context['total_students'])
        context['occupancy_rate'] = round(
            (context['total_students'] / total_capacity * 100) if total_capacity > 0 else 0, 1
        )

        # Bo'sh xonalar
        context['empty_rooms'] = rooms_qs.filter(status='available').count()
        context['full_rooms'] = rooms_qs.filter(status='full').count()
        context['partial_rooms'] = rooms_qs.filter(status='partial').count()

        # Moliya filtr
        payment_filter = {'status': 'completed'}
        invoice_filter = {'status__in': ['pending', 'partial', 'overdue']}
        if student_bld_filter:
            payment_filter['student__room__floor__building_id'] = user.building_id
            invoice_filter['student__room__floor__building_id'] = user.building_id

        # Moliya - bu oy
        context['total_collected_month'] = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            **payment_filter
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Moliya - bugun
        context['total_collected_today'] = Payment.objects.filter(
            payment_date__date=today,
            **payment_filter
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Kutilayotgan to'lovlar
        context['pending_amount'] = Invoice.objects.filter(
            **invoice_filter
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Qarzdorlar
        context['debtors_count'] = students_qs.annotate(
            total_invoiced=Sum('invoices__amount'),
            total_paid=Sum('payments__amount', filter=Q(payments__status='completed'))
        ).filter(
            total_invoiced__gt=0
        ).exclude(
            total_paid__gte=F('total_invoiced')
        ).count()

        # Davomat
        att_filter = {'date': today}
        if student_bld_filter:
            att_filter['student__room__floor__building_id'] = user.building_id
        today_att = Attendance.objects.filter(**att_filter)
        context['today_present'] = today_att.filter(status='present').count()
        context['today_absent'] = today_att.filter(status='absent').count()
        context['today_attendance'] = context['today_present']
        context['attendance_rate'] = round(
            (context['today_present'] / context['total_students'] * 100)
            if context['total_students'] > 0 else 0, 1
        )

        # Binolar bandlik ma'lumoti
        buildings = Building.objects.filter(is_active=True, **bld_filter)
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
        context['rooms_by_status'] = rooms_qs.values('status').annotate(
            count=Count('id')
        )

        # Qarzdorlar ro'yxati (bino bo'yicha filter bilan)
        selected_building = self.request.GET.get('debtor_building', '')
        debtors_qs = Student.objects.filter(is_active=True, **student_bld_filter)
        if selected_building:
            debtors_qs = debtors_qs.filter(room__floor__building_id=selected_building)
        debtors_qs = debtors_qs.annotate(
            total_invoiced=Coalesce(Sum('invoices__amount'), Value(0, output_field=DecimalField())),
            total_paid=Coalesce(
                Sum('payments__amount', filter=Q(payments__status='completed')),
                Value(0, output_field=DecimalField())
            )
        ).annotate(
            debt=F('total_invoiced') - F('total_paid')
        ).filter(
            debt__gt=0
        ).select_related('room', 'room__floor', 'room__floor__building').order_by('-debt')[:20]
        context['debtors_list'] = debtors_qs
        context['selected_debtor_building'] = selected_building
        context['all_buildings'] = Building.objects.filter(is_active=True, **bld_filter)

        return context


# Building Views
class BuildingListView(BuildingStaffMixin, ListView):
    model = Building
    template_name = 'buildings/building_list.html'
    context_object_name = 'buildings'

    def get_queryset(self):
        return self.get_buildings_qs().prefetch_related('floors', 'floors__rooms')


class BuildingDetailView(BuildingStaffMixin, DetailView):
    model = Building
    template_name = 'buildings/building_detail.html'
    context_object_name = 'building'

    def get_queryset(self):
        return self.get_buildings_qs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building = self.object

        floors_qs = building.floors.filter(is_active=True).order_by('number')

        floor_data = []
        building_total_capacity = 0
        building_occupied_beds = 0
        building_total_rooms = 0
        building_empty_rooms = 0
        building_partial_rooms = 0
        building_full_rooms = 0

        for floor in floors_qs:
            students = list(Student.objects.filter(
                room__floor=floor, is_active=True
            ).select_related('room').order_by('room__number', 'last_name'))

            rooms_grouped = []
            for room, room_students in groupby(students, key=lambda s: s.room):
                rooms_grouped.append({
                    'room': room,
                    'students': list(room_students),
                })

            # Har qavatdagi barcha xonalar statistikasi
            all_rooms = list(floor.rooms.filter(is_active=True).order_by('number').annotate(
                current_students=Count('students', filter=Q(students__is_active=True))
            ))
            empty_rooms = [r for r in all_rooms if r.current_students == 0]
            partial_rooms = [r for r in all_rooms if 0 < r.current_students < r.capacity]
            full_rooms = [r for r in all_rooms if r.current_students >= r.capacity]

            floor_total_capacity = floor.total_capacity
            floor_occupied = floor.occupied_beds

            building_total_capacity += floor_total_capacity
            building_occupied_beds += floor_occupied
            building_total_rooms += len(all_rooms)
            building_empty_rooms += len(empty_rooms)
            building_partial_rooms += len(partial_rooms)
            building_full_rooms += len(full_rooms)

            floor_data.append({
                'floor': floor,
                'student_count': len(students),
                'rooms_grouped': rooms_grouped,
                'total_rooms': floor.total_rooms,
                'total_capacity': floor_total_capacity,
                'occupied_beds': floor_occupied,
                'all_rooms': all_rooms,
                'empty_rooms': empty_rooms,
                'partial_rooms': partial_rooms,
                'full_rooms': full_rooms,
            })

        context['floor_data'] = floor_data

        # Bino umumiy statistikasi
        context['building_total_capacity'] = building_total_capacity
        context['building_occupied_beds'] = building_occupied_beds
        context['building_free_beds'] = building_total_capacity - building_occupied_beds
        context['building_total_rooms'] = building_total_rooms
        context['building_empty_rooms'] = building_empty_rooms
        context['building_partial_rooms'] = building_partial_rooms
        context['building_full_rooms'] = building_full_rooms
        context['building_occupancy_rate'] = round(
            (building_occupied_beds / building_total_capacity * 100) if building_total_capacity > 0 else 0
        )

        # Oxirgi 20 ta talaba (shu bino uchun)
        context['recent_students'] = Student.objects.filter(
            is_active=True, room__floor__building=building
        ).select_related('room', 'room__floor').order_by('-id')[:20]

        return context

class BuildingStatsView(BuildingStaffMixin, DetailView):
    model = Building
    template_name = 'buildings/building_stats.html'
    context_object_name = 'building'

    def get_queryset(self):
        return self.get_buildings_qs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building = self.object

        floors_qs = building.floors.filter(is_active=True).order_by('number')

        floor_data = []
        building_total_capacity = 0
        building_occupied_beds = 0
        building_total_rooms = 0
        building_empty_rooms = 0
        building_partial_rooms = 0
        building_full_rooms = 0

        for floor in floors_qs:
            all_rooms = list(floor.rooms.filter(is_active=True).order_by('number').annotate(
                current_students=Count('students', filter=Q(students__is_active=True))
            ))
            empty_rooms = [r for r in all_rooms if r.current_students == 0]
            partial_rooms = [r for r in all_rooms if 0 < r.current_students < r.capacity]
            full_rooms = [r for r in all_rooms if r.current_students >= r.capacity]

            student_count = sum(r.current_students for r in all_rooms)
            floor_total_capacity = sum(r.capacity for r in all_rooms)
            floor_occupied = student_count

            building_total_capacity += floor_total_capacity
            building_occupied_beds += floor_occupied
            building_total_rooms += len(all_rooms)
            building_empty_rooms += len(empty_rooms)
            building_partial_rooms += len(partial_rooms)
            building_full_rooms += len(full_rooms)

            floor_data.append({
                'floor': floor,
                'student_count': student_count,
                'total_rooms': len(all_rooms),
                'total_capacity': floor_total_capacity,
                'occupied_beds': floor_occupied,
                'all_rooms': all_rooms,
                'empty_rooms': empty_rooms,
                'partial_rooms': partial_rooms,
                'full_rooms': full_rooms,
            })

        context['floor_data'] = floor_data
        context['building_total_capacity'] = building_total_capacity
        context['building_occupied_beds'] = building_occupied_beds
        context['building_free_beds'] = building_total_capacity - building_occupied_beds
        context['building_total_rooms'] = building_total_rooms
        context['building_empty_rooms'] = building_empty_rooms
        context['building_partial_rooms'] = building_partial_rooms
        context['building_full_rooms'] = building_full_rooms
        context['building_occupancy_rate'] = round(
            (building_occupied_beds / building_total_capacity * 100) if building_total_capacity > 0 else 0
        )

        return context


class BuildingCreateView(SuperuserRequiredMixin, BuildingStaffMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('buildings:building_list')

    def form_valid(self, form):
        messages.success(self.request, 'Bino muvaffaqiyatli yaratildi')
        return super().form_valid(form)


class BuildingUpdateView(SuperuserRequiredMixin, BuildingStaffMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('buildings:building_list')

    def get_queryset(self):
        return self.get_buildings_qs()

    def form_valid(self, form):
        messages.success(self.request, 'Bino muvaffaqiyatli yangilandi')
        return super().form_valid(form)


class BuildingDeleteView(SuperuserRequiredMixin, BuildingStaffMixin, DeleteView):
    model = Building
    template_name = 'buildings/building_confirm_delete.html'
    success_url = reverse_lazy('buildings:building_list')

    def get_queryset(self):
        return self.get_buildings_qs()

    def form_valid(self, form):
        messages.success(self.request, 'Bino o\'chirildi')
        return super().form_valid(form)


# Floor Views
class FloorListView(BuildingStaffMixin, ListView):
    model = Floor
    template_name = 'buildings/floor_list.html'
    context_object_name = 'floors'

    def get_queryset(self):
        self.building = get_object_or_404(self.get_buildings_qs(), pk=self.kwargs['building_pk'])
        return self.get_floors_qs().filter(building=self.building).prefetch_related('rooms')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['building'] = self.building
        return context


class FloorCreateView(ManagePermissionMixin, BuildingStaffMixin, CreateView):
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


class FloorUpdateView(ManagePermissionMixin, BuildingStaffMixin, UpdateView):
    model = Floor
    form_class = FloorForm
    template_name = 'buildings/floor_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Etaj muvaffaqiyatli yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.building.pk})


class FloorDeleteView(ManagePermissionMixin, BuildingStaffMixin, DeleteView):
    model = Floor
    template_name = 'buildings/floor_confirm_delete.html'

    def get_success_url(self):
        return reverse('buildings:building_detail', kwargs={'pk': self.object.building.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Etaj o\'chirildi')
        return super().form_valid(form)


# Room Views
class RoomListView(BuildingStaffMixin, ListView):
    model = Room
    template_name = 'buildings/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 20

    def get_queryset(self):
        queryset = self.get_rooms_qs().select_related(
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
        context['buildings'] = self.get_buildings_qs()
        context['room_statuses'] = Room.RoomStatus.choices
        context['room_types'] = Room.RoomType.choices
        return context


class RoomDetailView(BuildingStaffMixin, DetailView):
    model = Room
    template_name = 'buildings/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        return self.get_rooms_qs()

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


class RoomCreateView(ManagePermissionMixin, BuildingStaffMixin, CreateView):
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


class RoomUpdateView(ManagePermissionMixin, BuildingStaffMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'buildings/room_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Xona muvaffaqiyatli yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('buildings:room_detail', kwargs={'pk': self.object.pk})


class RoomDeleteView(ManagePermissionMixin, BuildingStaffMixin, DeleteView):
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
    floors = Floor.objects.filter(building_id=building_id, is_active=True).values('id', 'number', 'gender')
    return JsonResponse(list(floors), safe=False)


@login_required
def get_rooms_api(request, floor_id):
    rooms = Room.objects.filter(floor_id=floor_id, is_active=True).values(
        'id', 'number', 'capacity', 'status'
    )
    return JsonResponse(list(rooms), safe=False)