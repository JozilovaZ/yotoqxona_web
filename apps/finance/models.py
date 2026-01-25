from django.db import models
from django.utils import timezone
from decimal import Decimal


class Invoice(models.Model):
    """Hisob-faktura (to'lov talabi)"""

    class InvoiceType(models.TextChoices):
        RENT = 'rent', 'Ijara to\'lovi'
        DEPOSIT = 'deposit', 'Depozit'
        UTILITIES = 'utilities', 'Kommunal xizmatlar'
        PENALTY = 'penalty', 'Jarima'
        OTHER = 'other', 'Boshqa'

    class InvoiceStatus(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        PARTIAL = 'partial', 'Qisman to\'langan'
        PAID = 'paid', 'To\'langan'
        OVERDUE = 'overdue', 'Muddati o\'tgan'
        CANCELLED = 'cancelled', 'Bekor qilingan'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="Talaba"
    )
    invoice_type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.RENT,
        verbose_name="Turi"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Summa"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")

    # Sanalar
    issue_date = models.DateField(default=timezone.now, verbose_name="Chiqarilgan sana")
    due_date = models.DateField(verbose_name="To'lov muddati")
    period_start = models.DateField(null=True, blank=True, verbose_name="Davr boshi")
    period_end = models.DateField(null=True, blank=True, verbose_name="Davr oxiri")

    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING,
        verbose_name="Holat"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hisob-faktura"
        verbose_name_plural = "Hisob-fakturalar"
        ordering = ['-issue_date']

    def __str__(self):
        return f"#{self.id} - {self.student} - {self.amount}"

    @property
    def paid_amount(self):
        """To'langan summa"""
        return self.payments.filter(
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    @property
    def remaining_amount(self):
        """Qolgan summa"""
        return max(Decimal('0'), self.amount - self.paid_amount)

    @property
    def is_overdue(self):
        """Muddati o'tganmi"""
        if self.status in ['paid', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date

    def update_status(self):
        """Statusni avtomatik yangilash"""
        if self.status == 'cancelled':
            return

        paid = self.paid_amount
        if paid >= self.amount:
            self.status = self.InvoiceStatus.PAID
        elif paid > 0:
            self.status = self.InvoiceStatus.PARTIAL
        elif self.is_overdue:
            self.status = self.InvoiceStatus.OVERDUE
        else:
            self.status = self.InvoiceStatus.PENDING
        self.save(update_fields=['status'])


class Payment(models.Model):
    """To'lov"""

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Naqd'
        CARD = 'card', 'Karta'
        TRANSFER = 'transfer', 'O\'tkazma'
        OTHER = 'other', 'Boshqa'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        COMPLETED = 'completed', 'Bajarildi'
        FAILED = 'failed', 'Muvaffaqiyatsiz'
        REFUNDED = 'refunded', 'Qaytarildi'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Talaba"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="Hisob-faktura"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Summa"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="To'lov usuli"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.COMPLETED,
        verbose_name="Holat"
    )

    payment_date = models.DateTimeField(default=timezone.now, verbose_name="To'lov sanasi")
    reference = models.CharField(max_length=100, blank=True, verbose_name="Referens")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Qabul qiluvchi"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.student} - {self.amount} - {self.payment_date.strftime('%d.%m.%Y')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invoice statusini yangilash
        if self.invoice:
            self.invoice.update_status()


class FinancialSummary(models.Model):
    """Oylik moliyaviy hisobot"""
    year = models.PositiveIntegerField(verbose_name="Yil")
    month = models.PositiveIntegerField(verbose_name="Oy")

    total_invoiced = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Jami hisoblangan"
    )
    total_collected = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Jami yig'ilgan"
    )
    total_debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Jami qarzdorlik"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Moliyaviy hisobot"
        verbose_name_plural = "Moliyaviy hisobotlar"
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.year}/{self.month}"