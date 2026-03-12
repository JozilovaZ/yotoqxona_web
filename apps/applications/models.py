from django.db import models
from django.conf import settings
from django.utils import timezone


class Application(models.Model):
    """Yotoqxonaga joylashish uchun ariza"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        PAYMENT_REQUIRED = 'payment_required', "To'lov kutilmoqda"
        PAID = 'paid', "To'lov qilindi"
        APPROVED = 'approved', 'Tasdiqlandi'
        REJECTED = 'rejected', 'Rad etildi'
        CANCELLED = 'cancelled', 'Bekor qilindi'

    # Ariza beruvchi
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Foydalanuvchi"
    )

    # Shaxsiy ma'lumotlar
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Otasining ismi")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    student_id = models.CharField(max_length=50, verbose_name="Talaba ID")
    faculty = models.CharField(max_length=200, blank=True, verbose_name="Fakultet")
    group = models.CharField(max_length=50, blank=True, verbose_name="Guruh")
    course = models.PositiveIntegerField(default=1, verbose_name="Kurs")

    # Tanlangan xona
    room = models.ForeignKey(
        'buildings.Room',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Tanlangan xona"
    )

    # Ariza holati
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Holati"
    )

    # Izoh
    message = models.TextField(blank=True, verbose_name="Xabar")
    admin_note = models.TextField(blank=True, verbose_name="Admin izohi")

    # To'lov
    payment_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name="To'lov summasi"
    )
    payment_confirmed = models.BooleanField(default=False, verbose_name="To'lov tasdiqlandi")

    # Admin
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_applications',
        verbose_name="Ko'rib chiqqan"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Ko'rib chiqilgan sana")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ariza"
        verbose_name_plural = "Arizalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.room} ({self.get_status_display()})"
