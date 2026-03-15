from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Student, RoomTransfer
from accounts.admin_mixins import BuildingFilteredFormMixin

try:
    from finance.models import Invoice
except ImportError:
    Invoice = None


# --- INLINES ---

class RoomTransferInline(admin.TabularInline):
    """Xona o'zgarishlari tarixi"""
    model = RoomTransfer
    fk_name = 'student'
    extra = 0
    fields = ('from_room', 'to_room', 'reason', 'transferred_at', 'transferred_by')
    readonly_fields = ('transferred_at', 'transferred_by', 'from_room', 'to_room', 'reason')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class InvoiceInline(admin.TabularInline):
    """Talabaning hisob-fakturalari (faqat ko'rish uchun)"""
    model = Invoice
    extra = 0
    fields = ('invoice_type', 'amount', 'status', 'issue_date', 'due_date')
    readonly_fields = ('invoice_type', 'amount', 'status', 'issue_date', 'due_date')
    show_change_link = True

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False


# --- ADMIN CLASSES ---

@admin.register(Student)
class StudentAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'room__floor__building'

    list_display = ('student_id', 'photo_thumbnail', 'full_name_display', 'phone', 'faculty_group', 'room_link',
                    'debt_status', 'is_active')
    list_display_links = ('student_id', 'full_name_display')
    list_filter = ('is_active', 'course', 'faculty', 'gender', 'check_in_date')
    search_fields = ('first_name', 'last_name', 'student_id', 'phone', 'room__number')
    autocomplete_fields = ['room']
    readonly_fields = ('days_stayed_display', 'total_paid_display', 'total_debt_display')

    inlines = [RoomTransferInline]
    if Invoice:
        inlines.append(InvoiceInline)

    fieldsets = (
        ("Shaxsiy ma'lumotlar", {
            'fields': (('first_name', 'last_name', 'middle_name'), ('gender', 'birth_date'), 'photo')
        }),
        ("Aloqa", {
            'fields': (('phone', 'email'), ('emergency_contact', 'emergency_phone'))
        }),
        ("O'qish joyi", {
            'fields': (('student_id', 'course'), ('faculty', 'group'))
        }),
        ("Yotoqxona", {
            'fields': ('room', ('check_in_date', 'check_out_date'), 'is_active', 'days_stayed_display')
        }),
        ("Moliya (Avtomatik hisoblangan)", {
            'fields': ('total_paid_display', 'total_debt_display')
        }),
        ("Qo'shimcha", {
            'fields': ('notes',)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    # --- Display Methods ---

    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                               obj.photo.url)
        return "---"
    photo_thumbnail.short_description = "Rasm"

    def full_name_display(self, obj):
        return f"{obj.last_name} {obj.first_name}"
    full_name_display.short_description = "F.I.SH"

    def faculty_group(self, obj):
        return f"{obj.faculty} | {obj.group}"
    faculty_group.short_description = "Fakultet / Guruh"

    def room_link(self, obj):
        if obj.room:
            return format_html(
                '<a href="/admin/buildings/room/{}/change/"><b>{}</b></a><br><span style="color:gray; font-size:10px">{}</span>',
                obj.room.id,
                obj.room.number,
                f"{obj.room.floor.number}-etaj"
            )
        return format_html('<span style="color: red;">Joylashmagan</span>')
    room_link.short_description = "Xona"

    def debt_status(self, obj):
        debt = obj.total_debt
        if debt > 0:
            return format_html(
                '<span style="color: white; background-color: #d32f2f; padding: 3px 6px; border-radius: 4px; font-weight: bold;">{:,} qarzdor</span>',
                int(debt)
            )
        return format_html('<span style="color: green; font-weight: bold;">Toza</span>')
    debt_status.short_description = "Qarzdorlik"

    def days_stayed_display(self, obj):
        return f"{obj.days_stayed} kun"
    days_stayed_display.short_description = "Yashagan muddati"

    def total_paid_display(self, obj):
        return f"{obj.total_paid:,.0f} so'm"
    total_paid_display.short_description = "Jami to'lagan"

    def total_debt_display(self, obj):
        debt = obj.total_debt
        color = "red" if debt > 0 else "green"
        return format_html('<span style="color: {}; font-weight: bold; font-size: 14px;">{:,} so\'m</span>', color, debt)
    total_debt_display.short_description = "Hozirgi qarz"


@admin.register(RoomTransfer)
class RoomTransferAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'student__room__floor__building'

    list_display = ('student', 'from_room', 'to_room', 'transferred_at', 'transferred_by')
    list_filter = ('transferred_at',)
    search_fields = ('student__first_name', 'student__last_name', 'reason')
    date_hierarchy = 'transferred_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
