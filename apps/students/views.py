from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.utils import timezone
from itertools import groupby

from .models import Student, RoomTransfer
from .forms import StudentForm, StudentTransferForm
from buildings.models import Room, Building, Floor
from accounts.view_mixins import BuildingStaffMixin, ManagePermissionMixin


class StudentListView(BuildingStaffMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 100

    def get_queryset(self):
        queryset = Student.objects.filter(is_active=True).select_related(
            'room', 'room__floor', 'room__floor__building'
        )

        # Bino bo'yicha filtr
        bid = self.get_user_building_id()
        if bid:
            queryset = queryset.filter(room__floor__building_id=bid)

        building_id = self.request.GET.get('building')
        if building_id:
            queryset = queryset.filter(room__floor__building_id=building_id)

        return queryset.order_by('room__floor__building', 'room__floor__number', 'room__number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['buildings'] = self.get_buildings_qs()

        # Qavatlar ro'yxati
        floors_qs = Floor.objects.filter(is_active=True).select_related('building').order_by('building', 'number')
        bid = self.get_user_building_id()
        if bid:
            floors_qs = floors_qs.filter(building_id=bid)

        building_id = self.request.GET.get('building')
        if building_id:
            floors_qs = floors_qs.filter(building_id=building_id)

        # Har bir qavat uchun statistika va talabalar
        floor_data = []
        for floor in floors_qs:
            students = list(Student.objects.filter(
                room__floor=floor, is_active=True
            ).select_related('room').order_by('room__number', 'last_name'))

            # Xona bo'yicha guruhlash
            rooms_grouped = []
            for room, room_students in groupby(students, key=lambda s: s.room):
                rooms_grouped.append({
                    'room': room,
                    'students': list(room_students),
                })

            floor_data.append({
                'floor': floor,
                'student_count': len(students),
                'students': students,
                'rooms_grouped': rooms_grouped,
                'total_rooms': floor.total_rooms,
                'total_capacity': floor.total_capacity,
                'occupied_beds': floor.occupied_beds,
            })

        context['floor_data'] = floor_data

        # Oxirgi 20 ta qo'shilgan talabalar
        recent_qs = Student.objects.filter(is_active=True).select_related(
            'room', 'room__floor', 'room__floor__building'
        ).order_by('-id')[:20]
        if bid:
            recent_qs = Student.objects.filter(
                is_active=True, room__floor__building_id=bid
            ).select_related('room', 'room__floor', 'room__floor__building').order_by('-id')[:20]
        if building_id:
            recent_qs = Student.objects.filter(
                is_active=True, room__floor__building_id=building_id
            ).select_related('room', 'room__floor', 'room__floor__building').order_by('-id')[:20]
        context['recent_students'] = recent_qs

        return context


class FloorStudentsView(BuildingStaffMixin, ListView):
    model = Student
    template_name = 'students/floor_students.html'
    context_object_name = 'students'

    def get_queryset(self):
        self.floor = get_object_or_404(Floor, pk=self.kwargs['floor_id'], is_active=True)
        queryset = Student.objects.filter(
            room__floor=self.floor, is_active=True
        ).select_related('room', 'room__floor', 'room__floor__building').order_by('room__number')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['floor'] = self.floor
        return context


class StudentDetailView(BuildingStaffMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        qs = Student.objects.all()
        return self.filter_by_building(qs, field='room__floor__building')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.object, 'payments'):
            context['payments'] = self.object.payments.all().order_by('-payment_date')[:10]
        if hasattr(self.object, 'invoices'):
            context['invoices'] = self.object.invoices.all().order_by('-issue_date')[:10]
        context['transfers'] = self.object.transfers.all().order_by('-transferred_at')[:5]
        return context


class StudentCreateView(ManagePermissionMixin, BuildingStaffMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['building_id'] = self.get_user_building_id()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Talaba muvaffaqiyatli ro\'yxatga olindi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('students:student_detail', kwargs={'pk': self.object.pk})


class StudentUpdateView(ManagePermissionMixin, BuildingStaffMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'

    def get_queryset(self):
        qs = Student.objects.all()
        return self.filter_by_building(qs, field='room__floor__building')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['building_id'] = self.get_user_building_id()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Talaba ma\'lumotlari yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('students:student_detail', kwargs={'pk': self.object.pk})


class StudentDeleteView(ManagePermissionMixin, BuildingStaffMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:student_list')

    def get_queryset(self):
        qs = Student.objects.all()
        return self.filter_by_building(qs, field='room__floor__building')

    def form_valid(self, form):
        messages.success(self.request, 'Talaba o\'chirildi')
        return super().form_valid(form)


class StudentTransferView(ManagePermissionMixin, BuildingStaffMixin, View):
    template_name = 'students/student_transfer.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentTransferForm(student=student, building_id=self.get_user_building_id())
        return render(request, self.template_name, {'student': student, 'form': form})

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentTransferForm(request.POST, student=student, building_id=self.get_user_building_id())

        if form.is_valid():
            new_room = form.cleaned_data['room']
            reason = form.cleaned_data.get('reason', '')
            old_room = student.room

            RoomTransfer.objects.create(
                student=student,
                from_room=old_room,
                to_room=new_room,
                reason=reason,
                transferred_by=request.user
            )

            student.room = new_room
            student.save()

            if old_room: old_room.update_status()
            new_room.update_status()

            messages.success(request, f'{student.first_name} ko\'chirildi')
            return redirect('students:student_detail', pk=pk)

        return render(request, self.template_name, {'student': student, 'form': form})


class StudentCheckoutView(ManagePermissionMixin, BuildingStaffMixin, View):
    template_name = 'students/student_checkout.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        return render(request, self.template_name, {'student': student})

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        old_room = student.room
        student.is_active = False
        student.check_out_date = timezone.now().date()
        student.room = None
        student.save()

        if old_room: old_room.update_status()

        messages.success(request, f'{student.first_name} chiqarildi')
        return redirect('students:student_list')


class TransferHistoryView(BuildingStaffMixin, ListView):
    model = RoomTransfer
    template_name = 'students/transfer_history.html'
    context_object_name = 'transfers'
    paginate_by = 20

    def get_queryset(self):
        qs = RoomTransfer.objects.all().order_by('-transferred_at')
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(
                Q(from_room__floor__building_id=bid) | Q(to_room__floor__building_id=bid)
            )
        return qs
