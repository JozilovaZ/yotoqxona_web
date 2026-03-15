from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Attendance, AttendanceReport
from accounts.admin_mixins import BuildingFilteredFormMixin


@admin.register(Attendance)
class AttendanceAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'student__room__floor__building'

    list_display = ('student', 'date', 'status', 'check_in_time', 'marked_by')
    list_filter = ('date', 'status', 'created_at')
    search_fields = ('student__first_name', 'student__last_name', 'notes')
    date_hierarchy = 'date'
    list_editable = ('status', 'check_in_time')
    autocomplete_fields = ['student']

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.marked_by:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)

    def status_colored(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'excused': 'blue',
            'leave': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Holat"


@admin.register(AttendanceReport)
class AttendanceReportAdmin(BuildingFilteredFormMixin, admin.ModelAdmin):
    building_filter_field = 'student__room__floor__building'

    list_display = ('student', 'year_month', 'total_days', 'attendance_rate_bar')
    list_filter = ('year', 'month')
    search_fields = ('student__first_name', 'student__last_name')
    readonly_fields = ('total_days', 'present_days', 'absent_days', 'late_days', 'excused_days', 'attendance_rate')

    actions = ['recalculate_reports']

    def year_month(self, obj):
        return f"{obj.year} - {obj.month:02d}"
    year_month.short_description = "Davr"

    def attendance_rate_bar(self, obj):
        percent = obj.attendance_rate
        if percent >= 90:
            color = "green"
        elif percent >= 70:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '''
            <div style="width: 100px; background: #e0e0e0; border-radius: 3px;">
                <div style="width: {}%; background: {}; height: 15px; border-radius: 3px;"></div>
            </div>
            <span>{}%</span>
            ''',
            percent,
            color,
            percent
        )
    attendance_rate_bar.short_description = "Davomat foizi"

    @admin.action(description="Tanlangan hisobotlarni qayta hisoblash")
    def recalculate_reports(self, request, queryset):
        for report in queryset:
            report.calculate()
        self.message_user(request, f"{queryset.count()} ta hisobot yangilandi.", messages.SUCCESS)
