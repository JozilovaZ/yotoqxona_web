from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import Invoice, Payment, FinancialSummary
from .forms import InvoiceForm, PaymentForm, BulkInvoiceForm
from students.models import Student
from accounts.view_mixins import BuildingStaffMixin, ManagePermissionMixin

from django.db.models import Prefetch


class FinanceDashboardView(BuildingStaffMixin, TemplateView):
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        bid = self.get_user_building_id()

        month_names = ["", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
                       "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]

        selected_month = int(self.request.GET.get('month', today.month))
        selected_year = int(self.request.GET.get('year', today.year))
        search_query = self.request.GET.get('search', '').strip()

        selected_month_name = month_names[selected_month]

        # Bino filtr
        payment_bld = {}
        invoice_bld = {}
        if bid:
            payment_bld = {'student__room__floor__building_id': bid}
            invoice_bld = {'student__room__floor__building_id': bid}

        # Statistikalar
        context['today_payments'] = \
        Payment.objects.filter(payment_date__date=today, status='completed', **payment_bld).aggregate(total=Sum('amount'))[
            'total'] or 0
        context['month_payments'] = \
        Payment.objects.filter(reference=selected_month_name, payment_date__year=selected_year,
                               status='completed', **payment_bld).aggregate(total=Sum('amount'))['total'] or 0
        context['pending_invoices'] = \
        Invoice.objects.filter(status__in=['pending', 'partial'], **invoice_bld).aggregate(total=Sum('amount'))['total'] or 0
        context['overdue_invoices'] = Invoice.objects.filter(status__in=['pending', 'partial', 'overdue'],
                                                             due_date__lt=today, **invoice_bld).count() or 0

        from buildings.models import Floor, Room
        floors_data = []

        # Bino admini faqat o'z binosi qavatlarini ko'radi
        floors_qs = self.get_floors_qs().order_by('number')

        for floor in floors_qs:
            rooms_list = []
            rooms = Room.objects.filter(floor=floor).order_by('number')

            for room in rooms:
                active_students = room.students.filter(is_active=True)

                if search_query:
                    active_students = active_students.filter(
                        Q(first_name__icontains=search_query) |
                        Q(last_name__icontains=search_query) |
                        Q(middle_name__icontains=search_query)
                    )

                student_count = active_students.count()

                if search_query and student_count == 0:
                    continue

                students_data = []
                for student in active_students:
                    payment = Payment.objects.filter(
                        student=student,
                        reference=selected_month_name,
                        status='completed'
                    ).first()
                    students_data.append({'obj': student, 'payment': payment})

                if students_data or not search_query:
                    rooms_list.append({
                        'number': room.number,
                        'students': students_data,
                        'rowspan': student_count if student_count > 0 else 1
                    })

            if rooms_list:
                floor_student_count = sum(len(r['students']) for r in rooms_list)
                floor_paid = sum(1 for r in rooms_list for s in r['students'] if s['payment'])
                floor_unpaid = floor_student_count - floor_paid
                floors_data.append({
                    'floor': floor,
                    'rooms': rooms_list,
                    'student_count': floor_student_count,
                    'paid_count': floor_paid,
                    'unpaid_count': floor_unpaid,
                })

        context.update({
            'floors_data': floors_data,
            'selected_month': selected_month,
            'selected_month_name': selected_month_name,
            'search_query': search_query,
            'months_range': [(i, name) for i, name in enumerate(month_names[1:], 1)]
        })
        return context


class InvoiceListView(BuildingStaffMixin, ListView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = Invoice.objects.select_related('student', 'student__room')
        bid = self.get_user_building_id()
        if bid:
            queryset = queryset.filter(student__room__floor__building_id=bid)

        status = self.request.GET.get('status')
        invoice_type = self.request.GET.get('type')
        student = self.request.GET.get('student')

        if status:
            queryset = queryset.filter(status=status)
        if invoice_type:
            queryset = queryset.filter(invoice_type=invoice_type)
        if student:
            queryset = queryset.filter(student_id=student)

        return queryset.order_by('-issue_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Invoice.InvoiceStatus.choices
        context['types'] = Invoice.InvoiceType.choices
        return context


class InvoiceDetailView(BuildingStaffMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        qs = Invoice.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(student__room__floor__building_id=bid)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        return context


class InvoiceCreateView(ManagePermissionMixin, BuildingStaffMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['building_id'] = self.get_user_building_id()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        student_id = self.request.GET.get('student')
        if student_id:
            initial['student'] = student_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Hisob-faktura yaratildi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('finance:invoice_detail', kwargs={'pk': self.object.pk})


class InvoiceUpdateView(ManagePermissionMixin, BuildingStaffMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'

    def get_queryset(self):
        qs = Invoice.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(student__room__floor__building_id=bid)
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['building_id'] = self.get_user_building_id()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Hisob-faktura yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('finance:invoice_detail', kwargs={'pk': self.object.pk})


class InvoiceDeleteView(ManagePermissionMixin, BuildingStaffMixin, DeleteView):
    model = Invoice
    template_name = 'finance/invoice_confirm_delete.html'
    success_url = reverse_lazy('finance:invoice_list')

    def get_queryset(self):
        qs = Invoice.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(student__room__floor__building_id=bid)
        return qs

    def form_valid(self, form):
        messages.success(self.request, 'Hisob-faktura o\'chirildi')
        return super().form_valid(form)


class BulkInvoiceCreateView(ManagePermissionMixin, BuildingStaffMixin, View):
    template_name = 'finance/invoice_bulk.html'

    def get(self, request):
        form = BulkInvoiceForm(building_id=self.get_user_building_id())
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BulkInvoiceForm(request.POST, building_id=self.get_user_building_id())
        if form.is_valid():
            students = Student.objects.filter(is_active=True, room__isnull=False)

            bid = self.get_user_building_id()
            if bid:
                students = students.filter(room__floor__building_id=bid)

            building = form.cleaned_data.get('building')
            floor = form.cleaned_data.get('floor')

            if building:
                students = students.filter(room__floor__building=building)
            if floor:
                students = students.filter(room__floor=floor)

            count = 0
            for student in students:
                Invoice.objects.create(
                    student=student,
                    invoice_type=form.cleaned_data['invoice_type'],
                    amount=form.cleaned_data['amount'],
                    due_date=form.cleaned_data['due_date'],
                    period_start=form.cleaned_data.get('period_start'),
                    period_end=form.cleaned_data.get('period_end'),
                    description=form.cleaned_data.get('description', '')
                )
                count += 1

            messages.success(request, f'{count} ta hisob-faktura yaratildi')
            return redirect('finance:invoice_list')

        return render(request, self.template_name, {'form': form})


class PaymentListView(BuildingStaffMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.select_related('student', 'invoice', 'received_by')
        bid = self.get_user_building_id()
        if bid:
            queryset = queryset.filter(student__room__floor__building_id=bid)

        method = self.request.GET.get('method')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if method:
            queryset = queryset.filter(payment_method=method)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(payment_date__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(payment_date__date__lte=date_to)

        return queryset.order_by('-payment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['methods'] = Payment.PaymentMethod.choices
        context['statuses'] = Payment.PaymentStatus.choices
        return context


class PaymentDetailView(BuildingStaffMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        qs = Payment.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(student__room__floor__building_id=bid)
        return qs


class PaymentCreateView(ManagePermissionMixin, BuildingStaffMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['building_id'] = self.get_user_building_id()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        student_id = self.request.GET.get('student')
        invoice_id = self.request.GET.get('invoice')
        if student_id:
            initial['student'] = student_id
        if invoice_id:
            initial['invoice'] = invoice_id
        return initial

    def form_valid(self, form):
        form.instance.received_by = self.request.user
        messages.success(self.request, 'To\'lov qabul qilindi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('finance:payment_detail', kwargs={'pk': self.object.pk})


class PaymentDeleteView(ManagePermissionMixin, BuildingStaffMixin, DeleteView):
    model = Payment
    template_name = 'finance/payment_confirm_delete.html'
    success_url = reverse_lazy('finance:payment_list')

    def get_queryset(self):
        qs = Payment.objects.all()
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(student__room__floor__building_id=bid)
        return qs

    def form_valid(self, form):
        messages.success(self.request, 'To\'lov o\'chirildi')
        return super().form_valid(form)


class DebtorListView(BuildingStaffMixin, ListView):
    template_name = 'finance/debtor_list.html'
    context_object_name = 'debtors'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField, Value
        qs = Student.objects.filter(is_active=True)
        bid = self.get_user_building_id()
        if bid:
            qs = qs.filter(room__floor__building_id=bid)
        return qs.annotate(
            total_invoiced=Coalesce(Sum('invoices__amount'), Value(0, output_field=DecimalField())),
            total_paid=Coalesce(
                Sum('payments__amount', filter=Q(payments__status='completed')),
                Value(0, output_field=DecimalField())
            )
        ).annotate(
            debt=F('total_invoiced') - F('total_paid')
        ).filter(
            debt__gt=0
        ).select_related('room', 'room__floor', 'room__floor__building').order_by('-debt')


class FinanceReportView(BuildingStaffMixin, TemplateView):
    template_name = 'finance/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        bid = self.get_user_building_id()

        bld_filter = {}
        if bid:
            bld_filter = {'student__room__floor__building_id': bid}

        # Yillik statistika
        context['yearly_stats'] = []
        for month in range(1, 13):
            month_data = {
                'month': month,
                'invoiced': Invoice.objects.filter(
                    issue_date__year=today.year,
                    issue_date__month=month,
                    **bld_filter
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'collected': Payment.objects.filter(
                    payment_date__year=today.year,
                    payment_date__month=month,
                    status='completed',
                    **bld_filter
                ).aggregate(total=Sum('amount'))['total'] or 0
            }
            context['yearly_stats'].append(month_data)

        return context
