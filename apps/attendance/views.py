from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, TemplateView, View
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

from .models import Attendance, AttendanceReport
from .forms import AttendanceForm, BulkAttendanceForm
from students.models import Student
from buildings.models import Building, Floor, Room
from accounts.view_mixins import BuildingStaffMixin


class AttendanceDashboardView(BuildingStaffMixin, TemplateView):
    template_name = 'attendance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        bid = self.get_user_building_id()

        student_filter = {}
        att_filter = {'date': today}
        if bid:
            student_filter = {'room__floor__building_id': bid}
            att_filter['student__room__floor__building_id'] = bid

        total_students = Student.objects.filter(is_active=True, **student_filter).count()

        # Bugungi davomat
        today_attendance = Attendance.objects.filter(**att_filter)
        context['present_count'] = today_attendance.filter(status='present').count()
        context['absent_count'] = today_attendance.filter(status='absent').count()
        context['late_count'] = today_attendance.filter(status='late').count()
        context['excused_count'] = today_attendance.filter(status='excused').count()

        context['unmarked_count'] = total_students - today_attendance.count()

        # Haftalik statistika
        week_start = today - timedelta(days=today.weekday())
        context['week_stats'] = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_filter = {'date': day}
            if bid:
                day_filter['student__room__floor__building_id'] = bid
            day_attendance = Attendance.objects.filter(**day_filter)
            context['week_stats'].append({
                'date': day,
                'present': day_attendance.filter(status='present').count(),
                'absent': day_attendance.filter(status='absent').count(),
            })

        context['buildings'] = self.get_buildings_qs()

        return context


class DailyAttendanceView(BuildingStaffMixin, TemplateView):
    template_name = 'attendance/daily.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bid = self.get_user_building_id()

        date_str = self.request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = timezone.now().date()

        context['selected_date'] = selected_date

        building_id = self.request.GET.get('building')
        floor_id = self.request.GET.get('floor')

        students = Student.objects.filter(is_active=True, room__isnull=False).select_related(
            'room', 'room__floor', 'room__floor__building'
        )

        # Bino admini faqat o'z binosi talabalarini ko'radi
        if bid:
            students = students.filter(room__floor__building_id=bid)

        if building_id:
            students = students.filter(room__floor__building_id=building_id)
        if floor_id:
            students = students.filter(room__floor_id=floor_id)

        attendance_dict = {}
        attendances = Attendance.objects.filter(date=selected_date)
        for att in attendances:
            attendance_dict[att.student_id] = att

        student_list = []
        for student in students.order_by('room__floor__building', 'room__floor__number', 'room__number', 'last_name'):
            student_list.append({
                'student': student,
                'attendance': attendance_dict.get(student.id)
            })

        context['student_list'] = student_list
        context['buildings'] = self.get_buildings_qs()
        context['statuses'] = Attendance.Status.choices

        if building_id:
            context['floors'] = Floor.objects.filter(building_id=building_id, is_active=True)
        elif bid:
            context['floors'] = Floor.objects.filter(building_id=bid, is_active=True)

        return context


class MarkAttendanceView(BuildingStaffMixin, View):
    def get(self, request):
        today = timezone.now().date()
        date_str = request.GET.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
        bid = self.get_user_building_id()

        floors_data = []
        floors = self.get_floors_qs().order_by('number')

        for floor in floors:
            rooms_list = []
            rooms = floor.rooms.all().order_by('number')

            for room in rooms:
                students = room.students.filter(is_active=True).order_by('last_name')
                if students.exists():
                    student_entries = []
                    for student in students:
                        attendance = Attendance.objects.filter(student=student, date=selected_date).first()
                        student_entries.append({
                            'obj': student,
                            'status': attendance.status if attendance else None
                        })

                    rooms_list.append({
                        'number': room.number,
                        'students': student_entries,
                        'rowspan': students.count()
                    })

            if rooms_list:
                floors_data.append({
                    'floor': floor,
                    'rooms': rooms_list
                })

        context = {
            'floors_data': floors_data,
            'selected_date': selected_date,
            'statuses': Attendance.Status.choices,
        }
        return render(request, 'attendance/daily.html', context)

    def post(self, request):
        date_str = request.POST.get('date')
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()

        for key, value in request.POST.items():
            if key.startswith('student_'):
                student_id = key.replace('student_', '')
                if value:
                    Attendance.objects.update_or_create(
                        student_id=student_id,
                        date=selected_date,
                        defaults={'status': value, 'marked_by': request.user}
                    )

        messages.success(request, 'Davomat saqlandi!')
        return redirect(f"{reverse('attendance:mark')}?date={selected_date}")


class AttendanceHistoryView(BuildingStaffMixin, ListView):
    model = Attendance
    template_name = 'attendance/history.html'
    context_object_name = 'attendances'
    paginate_by = 50

    def get_queryset(self):
        queryset = Attendance.objects.select_related('student', 'student__room', 'marked_by')
        bid = self.get_user_building_id()
        if bid:
            queryset = queryset.filter(student__room__floor__building_id=bid)

        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-date', 'student__last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Attendance.Status.choices
        return context


class StudentAttendanceView(BuildingStaffMixin, TemplateView):
    template_name = 'attendance/student_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'])
        context['student'] = student

        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        context['year'] = year
        context['month'] = month
        context['month_name'] = calendar.month_name[month]

        _, num_days = calendar.monthrange(year, month)
        days = []
        for day in range(1, num_days + 1):
            date = datetime(year, month, day).date()
            attendance = Attendance.objects.filter(student=student, date=date).first()
            days.append({
                'date': date,
                'attendance': attendance
            })

        context['days'] = days

        month_attendances = Attendance.objects.filter(
            student=student,
            date__year=year,
            date__month=month
        )
        context['present_days'] = month_attendances.filter(status='present').count()
        context['absent_days'] = month_attendances.filter(status='absent').count()
        context['late_days'] = month_attendances.filter(status='late').count()
        context['excused_days'] = month_attendances.filter(status='excused').count()

        return context


class FloorAttendanceView(BuildingStaffMixin, TemplateView):
    template_name = 'attendance/floor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        floor = get_object_or_404(self.get_floors_qs(), pk=self.kwargs['floor_pk'])
        context['floor'] = floor

        date_str = self.request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = timezone.now().date()

        context['selected_date'] = selected_date

        rooms = Room.objects.filter(floor=floor, is_active=True).prefetch_related('students')

        room_list = []
        for room in rooms:
            students = room.students.filter(is_active=True)
            student_data = []
            for student in students:
                attendance = Attendance.objects.filter(student=student, date=selected_date).first()
                student_data.append({
                    'student': student,
                    'attendance': attendance
                })
            room_list.append({
                'room': room,
                'students': student_data
            })

        context['rooms'] = room_list
        context['statuses'] = Attendance.Status.choices

        return context


class AttendanceReportView(BuildingStaffMixin, TemplateView):
    template_name = 'attendance/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bid = self.get_user_building_id()

        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        context['year'] = year
        context['month'] = month
        context['month_name'] = calendar.month_name[month]

        students = Student.objects.filter(is_active=True).select_related('room')
        if bid:
            students = students.filter(room__floor__building_id=bid)

        att_filter = {
            'date__year': year,
            'date__month': month,
            'student__is_active': True
        }
        if bid:
            att_filter['student__room__floor__building_id'] = bid

        all_attendances = Attendance.objects.filter(**att_filter).values('student_id', 'status')

        from collections import defaultdict
        att_map = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'total': 0})
        for att in all_attendances:
            sid = att['student_id']
            att_map[sid]['total'] += 1
            if att['status'] in att_map[sid]:
                att_map[sid][att['status']] += 1

        student_stats = []
        for student in students:
            data = att_map[student.id]
            present = data['present']
            absent = data['absent']
            late = data['late']
            total = data['total']
            rate = round((present + late) / total * 100, 1) if total > 0 else 0
            student_stats.append({
                'student': student,
                'present': present,
                'absent': absent,
                'late': late,
                'total': total,
                'rate': rate
            })

        student_stats.sort(key=lambda x: x['rate'], reverse=True)
        context['student_stats'] = student_stats

        return context
