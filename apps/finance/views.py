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
from apps.students.models import Student


class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Bugungi statistika
        context['today_payments'] = Payment.objects.filter(
            payment_date__date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Oylik statistika
        context['month_payments'] = Payment.objects.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Kutilayotgan to'lovlar
        context['pending_invoices'] = Invoice.objects.filter(
            status__in=['pending', 'partial']
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Muddati o'tgan
        context['overdue_invoices'] = Invoice.objects.filter(
            status__in=['pending', 'partial', 'overdue'],
            due_date__lt=today
        ).count()

        # Oxirgi to'lovlar
        context['recent_payments'] = Payment.objects.filter(
            status='completed'
        ).select_related('student', 'invoice').order_by('-payment_date')[:10]

        # Qarzdorlar
        context['top_debtors'] = Student.objects.filter(
            is_active=True
        ).annotate(
            debt=Sum('invoices__amount') - Sum('payments__amount', filter=Q(payments__status='completed'))
        ).filter(debt__gt=0).order_by('-debt')[:5]

        return context


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = Invoice.objects.select_related('student', 'student__room')

        # Filtrlash
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


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'finance/invoice_detail.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        return context


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'

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


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'finance/invoice_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Hisob-faktura yangilandi')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('finance:invoice_detail', kwargs={'pk': self.object.pk})


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'finance/invoice_confirm_delete.html'
    success_url = reverse_lazy('finance:invoice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Hisob-faktura o\'chirildi')
        return super().form_valid(form)


class BulkInvoiceCreateView(LoginRequiredMixin, View):
    template_name = 'finance/invoice_bulk.html'

    def get(self, request):
        form = BulkInvoiceForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BulkInvoiceForm(request.POST)
        if form.is_valid():
            students = Student.objects.filter(is_active=True, room__isnull=False)

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


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.select_related('student', 'invoice', 'received_by')

        # Filtrlash
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


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'

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


class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'finance/payment_confirm_delete.html'
    success_url = reverse_lazy('finance:payment_list')

    def form_valid(self, form):
        messages.success(self.request, 'To\'lov o\'chirildi')
        return super().form_valid(form)


class DebtorListView(LoginRequiredMixin, ListView):
    template_name = 'finance/debtor_list.html'
    context_object_name = 'debtors'
    paginate_by = 20

    def get_queryset(self):
        return Student.objects.filter(
            is_active=True
        ).annotate(
            total_invoiced=Sum('invoices__amount'),
            total_paid=Sum('payments__amount', filter=Q(payments__status='completed'))
        ).annotate(
            debt=F('total_invoiced') - F('total_paid')
        ).filter(
            debt__gt=0
        ).select_related('room', 'room__floor', 'room__floor__building').order_by('-debt')


class FinanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Yillik statistika
        context['yearly_stats'] = []
        for month in range(1, 13):
            month_data = {
                'month': month,
                'invoiced': Invoice.objects.filter(
                    issue_date__year=today.year,
                    issue_date__month=month
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'collected': Payment.objects.filter(
                    payment_date__year=today.year,
                    payment_date__month=month,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0
            }
            context['yearly_stats'].append(month_data)

        return context