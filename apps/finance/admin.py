from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Q
from django.contrib import messages
from .models import Invoice, Payment, FinancialSummary
from accounts.admin_mixins import BuildingFilteredFormMixin


# --- INLINES ---

class PaymentInline(admin.TabularInline):
    """Invoice ichida to'lovlarni ko'rsatish"""
    model = Payment
    extra = 0
    fields = ('amount', 'payment_method', 'status', 'payment_date', 'received_by')
    readonly_fields = ('payment_date', 'received_by')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


# --- ADMIN CLASSES ---

@admin.register(Invoice)
class InvoiceAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'student__room__floor__building'

    list_display = ('id_display', 'student_link', 'invoice_type', 'amount_fmt', 'paid_fmt', 'remaining_fmt',
                    'status_colored', 'due_date')
    list_display_links = ('id_display', 'student_link')
    list_filter = ('status', 'invoice_type', 'issue_date', 'due_date')
    search_fields = ('student__first_name', 'student__last_name', 'description', 'id')
    autocomplete_fields = ['student']
    readonly_fields = ('paid_amount_display', 'remaining_amount_display')
    inlines = [PaymentInline]

    date_hierarchy = 'issue_date'

    fieldsets = (
        ("Asosiy ma'lumot", {
            'fields': ('student', 'invoice_type', 'status')
        }),
        ("Summa", {
            'fields': ('amount', 'paid_amount_display', 'remaining_amount_display')
        }),
        ("Muddatlar", {
            'fields': ('issue_date', 'due_date', 'period_start', 'period_end')
        }),
        ("Qo'shimcha", {
            'fields': ('description',)
        }),
    )

    def id_display(self, obj):
        return f"INV-{obj.id:05d}"
    id_display.short_description = "ID"

    def student_link(self, obj):
        return obj.student
    student_link.short_description = "Talaba"

    def amount_fmt(self, obj):
        return f"{obj.amount:,.0f}"
    amount_fmt.short_description = "Jami Summa"

    def paid_fmt(self, obj):
        return f"{obj.paid_amount:,.0f}"
    paid_fmt.short_description = "To'langan"

    def remaining_fmt(self, obj):
        val = obj.remaining_amount
        color = "red" if val > 0 else "green"
        return format_html('<span style="color: {}">{}</span>', color, f"{val:,.0f}")
    remaining_fmt.short_description = "Qoldiq"

    def paid_amount_display(self, obj):
        return f"{obj.paid_amount:,.2f}"
    paid_amount_display.short_description = "To'langan summa"

    def remaining_amount_display(self, obj):
        return f"{obj.remaining_amount:,.2f}"
    remaining_amount_display.short_description = "Qolgan summa"

    def status_colored(self, obj):
        colors = {
            'paid': 'green',
            'pending': 'orange',
            'overdue': 'red',
            'partial': 'blue',
            'cancelled': 'gray',
        }
        if obj.is_overdue and obj.status != 'paid':
            color = 'red'
            text = "MUDDATI O'TGAN"
        else:
            color = colors.get(obj.status, 'black')
            text = obj.get_status_display()

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, text.upper()
        )
    status_colored.short_description = "Holat"


@admin.register(Payment)
class PaymentAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'student__room__floor__building'

    list_display = ('student', 'amount_fmt', 'payment_method', 'status_icon', 'payment_date', 'invoice_link',
                    'received_by')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('student__first_name', 'student__last_name', 'reference')
    autocomplete_fields = ['student', 'invoice']

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.received_by:
            obj.received_by = request.user
        super().save_model(request, obj, form, change)

    def amount_fmt(self, obj):
        return f"{obj.amount:,.0f}"
    amount_fmt.short_description = "Summa"

    def invoice_link(self, obj):
        if obj.invoice:
            return format_html('<a href="/admin/finance/invoice/{}/change/">INV-{:05d}</a>', obj.invoice.id,
                               obj.invoice.id)
        return "-"
    invoice_link.short_description = "Invoice"

    def status_icon(self, obj):
        icons = {
            'completed': '---',
            'pending': '...',
            'failed': 'X',
            'refunded': '<-',
        }
        return icons.get(obj.status, '') + " " + obj.get_status_display()
    status_icon.short_description = "Holat"


@admin.register(FinancialSummary)
class FinancialSummaryAdmin(admin.ModelAdmin):
    list_display = ('year_month', 'total_invoiced_fmt', 'total_collected_fmt', 'total_debt_fmt', 'created_at')
    list_filter = ('year', 'month')
    readonly_fields = ('total_invoiced', 'total_collected', 'total_debt')

    actions = ['calculate_summary']

    def year_month(self, obj):
        return f"{obj.year} - {obj.month:02d}"
    year_month.short_description = "Davr"

    def total_invoiced_fmt(self, obj):
        return f"{obj.total_invoiced:,.0f}"
    total_invoiced_fmt.short_description = "Hisoblangan"

    def total_collected_fmt(self, obj):
        return format_html('<b style="color: green;">{}</b>', f"{obj.total_collected:,.0f}")
    total_collected_fmt.short_description = "Yig'ilgan"

    def total_debt_fmt(self, obj):
        return format_html('<b style="color: red;">{}</b>', f"{obj.total_debt:,.0f}")
    total_debt_fmt.short_description = "Qarzdorlik"

    @admin.action(description="Tanlangan oylar uchun hisobotni qayta shakllantirish")
    def calculate_summary(self, request, queryset):
        for summary in queryset:
            invoices_sum = Invoice.objects.filter(
                issue_date__year=summary.year,
                issue_date__month=summary.month
            ).aggregate(total=Sum('amount'))['total'] or 0

            payments_sum = Payment.objects.filter(
                payment_date__year=summary.year,
                payment_date__month=summary.month,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0

            summary.total_invoiced = invoices_sum
            summary.total_collected = payments_sum
            summary.total_debt = invoices_sum - payments_sum
            summary.save()

        self.message_user(request, "Moliyaviy hisobotlar muvaffaqiyatli yangilandi!", messages.SUCCESS)
