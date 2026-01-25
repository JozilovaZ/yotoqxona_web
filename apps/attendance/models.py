from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    """Davomat yozuvi"""

    class Status(models.TextChoices):
        PRESENT = 'present', 'Bor'
        ABSENT = 'absent', 'Yo\'q'
        LATE = 'late', 'Kechikkan'
        EXCUSED = 'excused', 'Sababli'
        LEAVE = 'leave', 'Ta\'tilda'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Talaba"
    )
    date = models.DateField(default=timezone.now, verbose_name="Sana")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
        verbose_name="Holat"
    )
    check_in_time = models.TimeField(null=True, blank=True, verbose_name="Kelish vaqti")
    check_out_time = models.TimeField(null=True, blank=True, verbose_name="Ketish vaqti")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    marked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Kim tomonidan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Davomat"
        verbose_name_plural = "Davomat"
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__last_name']

    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"


class AttendanceReport(models.Model):
    """Oylik davomat hisoboti"""
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_reports',
        verbose_name="Talaba"
    )
    year = models.PositiveIntegerField(verbose_name="Yil")
    month = models.PositiveIntegerField(verbose_name="Oy")

    total_days = models.PositiveIntegerField(default=0, verbose_name="Jami kunlar")
    present_days = models.PositiveIntegerField(default=0, verbose_name="Kelgan kunlar")
    absent_days = models.PositiveIntegerField(default=0, verbose_name="Kelmagan kunlar")
    late_days = models.PositiveIntegerField(default=0, verbose_name="Kechikkan kunlar")
    excused_days = models.PositiveIntegerField(default=0, verbose_name="Sababli kunlar")

    attendance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Davomat foizi"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Davomat hisoboti"
        verbose_name_plural = "Davomat hisobotlari"
        unique_together = ['student', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.student} - {self.year}/{self.month}"

    def calculate(self):
        """Hisobotni qayta hisoblash"""
        attendances = Attendance.objects.filter(
            student=self.student,
            date__year=self.year,
            date__month=self.month
        )

        self.total_days = attendances.count()
        self.present_days = attendances.filter(status='present').count()
        self.absent_days = attendances.filter(status='absent').count()
        self.late_days = attendances.filter(status='late').count()
        self.excused_days = attendances.filter(status='excused').count()

        if self.total_days > 0:
            self.attendance_rate = (self.present_days + self.late_days) / self.total_days * 100
        else:
            self.attendance_rate = 0

        self.save()