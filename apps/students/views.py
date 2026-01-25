from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.utils import timezone

from .models import Student, RoomTransfer
from .forms import StudentForm, StudentTransferForm
from apps.buildings.models import Room


class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = Student.objects.filter(is_active=True).select_related(
            'room', 'room__floor', 'room__floor__building'
        )

        # Qidiruv
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(student_id__icontains=search) |
                Q(phone__icontains=search) |
                Q(group__icontains=search)
            )

        # Filtrlash
        building = self.request.GET.get('building')
        floor = self.request.GET.get('floor')

        if building:
            queryset = queryset.filter(room__floor__building_id=building)
        if floor:
            queryset = queryset.filter(room__floor_id=floor)

        return queryset.order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.buildings.models import Building
        context['buildings'] = Building.objects.filter(is_active=True)
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('-payment_date')[:10]
        context['invoices'] = self.object.invoices.all().order_by('-issue_date')[:10]
        context['transfers'] = self.object.transfers.all().order_by('-transferred_at')[:5]
        context['attendances'] = self.object.attendances.all().order_by('-date')[:30]
        return context


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Talaba muvaffaqiyatli ro\'yxatga olindi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('students:student_detail', kwargs={'pk': self.object.pk})


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Talaba ma\'lumotlari yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('students:student_detail', kwargs={'pk': self.object.pk})


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('students:student_list')

    def form_valid(self, form):
        messages.success(self.request, 'Talaba o\'chirildi')
        return super().form_valid(form)


class StudentTransferView(LoginRequiredMixin, View):
    template_name = 'students/student_transfer.html'

    def get(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentTransferForm(student=student)
        return render(request, self.template_name, {'student': student, 'form': form})

    def post(self, request, pk):
        student = get_object_or_404(Student, pk=pk)
        form = StudentTransferForm(request.POST, student=student)

        if form.is_valid():
            new_room = form.cleaned_data['room']
            reason = form.cleaned_data.get('reason', '')

            old_room = student.room

            # Transfer yaratish
            RoomTransfer.objects.create(
                student=student,
                from_room=old_room,
                to_room=new_room,
                reason=reason,
                transferred_by=request.user
            )

            # Talabani yangi xonaga o'tkazish
            student.room = new_room
            student.save()

            # Xonalar statusini yangilash
            if old_room:
                old_room.update_status()
            new_room.update_status()

            messages.success(request, f'{student.full_name} muvaffaqiyatli ko\'chirildi')
            return redirect('students:student_detail', pk=pk)

        return render(request, self.template_name, {'student': student, 'form': form})


class StudentCheckoutView(LoginRequiredMixin, View):
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

        if old_room:
            old_room.update_status()

        messages.success(request, f'{student.full_name} yotoqxonadan chiqarildi')
        return redirect('students:student_list')


class TransferHistoryView(LoginRequiredMixin, ListView):
    model = RoomTransfer
    template_name = 'students/transfer_history.html'
    context_object_name = 'transfers'
    paginate_by = 20
    ordering = ['-transferred_at']