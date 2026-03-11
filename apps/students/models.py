from django.db import models
from django.utils import timezone
from django.apps import apps  # Modelni xavfsiz chaqirish uchun
from dateutil.relativedelta import relativedelta
import datetime


class Student(models.Model):
    """Talaba modeli"""

    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    # Shaxsiy ma'lumotlar
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Otasining ismi")
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.MALE,
        verbose_name="Jinsi"
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Tug'ilgan sana")
    photo = models.ImageField(upload_to='students/', blank=True, null=True, verbose_name="Rasm")

    # Aloqa ma'lumotlari
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name="Favqulodda aloqa")
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name="Favqulodda telefon")

    # O'quv ma'lumotlari
    student_id = models.CharField(max_length=50, unique=True, verbose_name="Talaba ID")
    faculty = models.CharField(max_length=200, blank=True, verbose_name="Fakultet")
    group = models.CharField(max_length=50, blank=True, verbose_name="Guruh")
    course = models.PositiveIntegerField(default=1, verbose_name="Kurs")

    # Yotoqxona ma'lumotlari
    room = models.ForeignKey(
        'buildings.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Xona"
    )
    check_in_date = models.DateField(default=timezone.now, verbose_name="Joylashgan sana")
    check_out_date = models.DateField(null=True, blank=True, verbose_name="Chiqish sanasi")

    # Holat
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Talaba"
        verbose_name_plural = "Talabalar"
        ordering = ['last_name', 'first_name']
        app_label = 'students'  # AppLabel muammosini oldini olish uchun

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    @property
    def months_stayed(self):
        """Necha oy yashagani (TypeError xatosiz)"""
        if not self.check_in_date:
            return 0

        # Date va Datetime farqini yo'qotish
        end_date = self.check_out_date or timezone.now().date()
        start_date = self.check_in_date

        if isinstance(start_date, datetime.datetime): start_date = start_date.date()
        if isinstance(end_date, datetime.datetime): end_date = end_date.date()

        delta = relativedelta(end_date, start_date)
        return delta.years * 12 + delta.months

    @property
    def days_stayed(self):
        """Necha kun yashagani (TypeError xatosiz)"""
        if not self.check_in_date:
            return 0

        end_date = self.check_out_date or timezone.now().date()
        start_date = self.check_in_date

        if isinstance(start_date, datetime.datetime): start_date = start_date.date()
        if isinstance(end_date, datetime.datetime): end_date = end_date.date()

        return (end_date - start_date).days

    @property
    def total_paid(self):
        """Jami to'langan summa (Circular import xatosiz)"""
        Payment = apps.get_model('finance', 'Payment')
        return Payment.objects.filter(
            student=self,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def total_debt(self):
        """Jami qarzdorlik (Circular import xatosiz)"""
        Invoice = apps.get_model('finance', 'Invoice')
        invoices = Invoice.objects.filter(student=self)
        total_invoiced = invoices.aggregate(total=models.Sum('amount'))['total'] or 0
        return max(0, total_invoiced - self.total_paid)

    @property
    def has_debt(self):
        return self.total_debt > 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Xona statusini yangilash (Faqat xona mavjud bo'lsa)
        if self.room:
            self.room.update_status()


# RoomTransfer modeli o'zgarishsiz qolishi mumkin,
# lekin 'accounts.User' va 'buildings.Room' string ko'rinishida chaqirilgani to'g'ri.
class RoomTransfer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transfers')
    from_room = models.ForeignKey('buildings.Room', on_delete=models.SET_NULL, null=True, related_name='transfers_from')
    to_room = models.ForeignKey('buildings.Room', on_delete=models.SET_NULL, null=True, related_name='transfers_to')
    reason = models.TextField(blank=True)
    transferred_at = models.DateTimeField(auto_now_add=True)
    transferred_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Xona ko'chirish"
        verbose_name_plural = "Xona ko'chirishlar"
        ordering = ['-transferred_at']