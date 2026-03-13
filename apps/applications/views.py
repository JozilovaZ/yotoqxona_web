from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Application
from .forms import ApplicationForm, ApplicationReviewForm
from buildings.models import Building, Floor, Room
from students.models import Student


class StudentHomeView(TemplateView):
    """Talaba uchun bosh sahifa (ochiq — login kerak emas)"""
    template_name = 'applications/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            user = self.request.user
            ctx['my_applications_count'] = Application.objects.filter(user=user).count()
            ctx['pending_application'] = Application.objects.filter(
                user=user, status__in=['pending', 'payment_required', 'paid']
            ).first()

        return ctx


class AvailableRoomsView(ListView):
    """Talabalar uchun yotoqxonalar ro'yxati"""
    template_name = 'applications/available_rooms.html'
    context_object_name = 'buildings'

    def get_queryset(self):
        return Building.objects.filter(is_active=True).prefetch_related(
            'floors__rooms'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        buildings_data = []
        for building in self.get_queryset():
            total_capacity = 0
            available_beds = 0
            total_rooms = 0
            for floor in building.floors.filter(is_active=True):
                for room in floor.rooms.filter(is_active=True):
                    total_rooms += 1
                    total_capacity += room.capacity
                    if room.status in ['available', 'partial']:
                        available_beds += room.available_beds
            buildings_data.append({
                'building': building,
                'total_rooms': total_rooms,
                'total_capacity': total_capacity,
                'available_beds': available_beds,
                'occupancy_rate': round((total_capacity - available_beds) / total_capacity * 100) if total_capacity > 0 else 0,
            })
        ctx['buildings_data'] = buildings_data
        return ctx


class BuildingDetailForApplicantView(DetailView):
    """Talaba uchun yotoqxona tafsilotlari va bo'sh xonalar"""
    model = Building
    template_name = 'applications/building_detail.html'
    context_object_name = 'building'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        building = self.object
        floors_data = []
        for floor in building.floors.filter(is_active=True).order_by('number'):
            rooms = floor.rooms.filter(
                is_active=True,
                status__in=['available', 'partial']
            ).order_by('number')
            if rooms.exists():
                floors_data.append({
                    'floor': floor,
                    'rooms': rooms,
                })
        ctx['floors_data'] = floors_data
        return ctx


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """Ariza topshirish"""
    model = Application
    form_class = ApplicationForm
    template_name = 'applications/application_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        messages.success(self.request, "Arizangiz muvaffaqiyatli topshirildi! Admin ko'rib chiqadi.")
        return redirect('applications:my_applications')

    def get_initial(self):
        initial = super().get_initial()
        room_id = self.request.GET.get('room')
        if room_id:
            try:
                room = Room.objects.get(pk=room_id)
                initial['room'] = room
                initial['building'] = room.floor.building
                initial['floor'] = room.floor
            except Room.DoesNotExist:
                pass
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        room_id = self.request.GET.get('room')
        if room_id:
            try:
                room = Room.objects.get(pk=room_id)
                form.fields['floor'].queryset = Floor.objects.filter(
                    building=room.floor.building, is_active=True
                )
                form.fields['room'].queryset = Room.objects.filter(
                    floor=room.floor, is_active=True,
                    status__in=['available', 'partial']
                )
            except Room.DoesNotExist:
                pass
        return form


class MyApplicationsView(LoginRequiredMixin, ListView):
    """Mening arizalarim"""
    template_name = 'applications/my_applications.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """Ariza tafsilotlari"""
    model = Application
    template_name = 'applications/application_detail.html'
    context_object_name = 'application'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff_member:
            return Application.objects.all()
        return Application.objects.filter(user=user)


# ─── ADMIN VIEWS ───

class ApplicationListView(LoginRequiredMixin, ListView):
    """Admin: barcha arizalar"""
    template_name = 'applications/admin_application_list.html'
    context_object_name = 'applications'

    def get_queryset(self):
        qs = Application.objects.select_related('room__floor__building', 'user')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['status_choices'] = Application.Status.choices
        ctx['pending_count'] = Application.objects.filter(status='pending').count()
        ctx['paid_count'] = Application.objects.filter(status='paid').count()
        return ctx


class ApplicationReviewView(LoginRequiredMixin, View):
    """Admin: arizani ko'rib chiqish"""

    def get(self, request, pk):
        app = get_object_or_404(Application, pk=pk)
        form = ApplicationReviewForm()
        return self._render(request, app, form)

    def post(self, request, pk):
        app = get_object_or_404(Application, pk=pk)
        form = ApplicationReviewForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data['action']
            app.admin_note = form.cleaned_data.get('admin_note', '')
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()

            if action == 'payment_required':
                app.status = Application.Status.PAYMENT_REQUIRED
                app.payment_amount = form.cleaned_data.get('payment_amount')
                messages.success(request, "Arizaga to'lov so'rovi yuborildi.")

            elif action == 'approved':
                app.status = Application.Status.APPROVED
                # Talabani xonaga joylashtirish
                self._place_student(app)
                messages.success(request, f"{app.first_name} {app.last_name} muvaffaqiyatli joylashtirildi!")

            elif action == 'rejected':
                app.status = Application.Status.REJECTED
                messages.info(request, "Ariza rad etildi.")

            app.save()
            return redirect('applications:admin_list')

        return self._render(request, app, form)

    def _render(self, request, app, form):
        from django.shortcuts import render
        return render(request, 'applications/admin_review.html', {
            'application': app,
            'form': form,
        })

    def _place_student(self, app):
        """Arizani tasdiqlanganda talabani xonaga joylashtirish"""
        student, created = Student.objects.get_or_create(
            student_id=app.student_id,
            defaults={
                'first_name': app.first_name,
                'last_name': app.last_name,
                'middle_name': app.middle_name,
                'phone': app.phone,
                'faculty': app.faculty,
                'group': app.group,
                'course': app.course,
                'room': app.room,
                'is_active': True,
            }
        )
        if not created:
            student.room = app.room
            student.is_active = True
            student.save()

        # User rolini RESIDENT ga o'zgartirish
        from accounts.models import User
        app.user.role = User.Role.RESIDENT
        app.user.save(update_fields=['role'])


class ConfirmPaymentView(LoginRequiredMixin, View):
    """Admin: to'lovni tasdiqlash"""

    def post(self, request, pk):
        app = get_object_or_404(Application, pk=pk)
        if app.status == Application.Status.PAYMENT_REQUIRED:
            app.status = Application.Status.PAID
            app.payment_confirmed = True
            app.save()
            messages.success(request, "To'lov tasdiqlandi. Endi arizani tasdiqlashingiz mumkin.")
        return redirect('applications:admin_review', pk=pk)


# ─── API ───

def get_floors_json(request, building_id):
    floors = Floor.objects.filter(building_id=building_id, is_active=True).order_by('number')
    data = [{'id': f.id, 'number': f.number} for f in floors]
    return JsonResponse(data, safe=False)


def get_rooms_json(request, floor_id):
    rooms = Room.objects.filter(
        floor_id=floor_id,
        is_active=True,
        status__in=['available', 'partial']
    ).order_by('number')
    data = [{
        'id': r.id,
        'number': r.number,
        'room_type': r.get_room_type_display(),
        'capacity': r.capacity,
        'available_beds': r.available_beds,
        'monthly_price': str(r.monthly_price),
    } for r in rooms]
    return JsonResponse(data, safe=False)
