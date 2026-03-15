from django.db import models
from django.utils import timezone


class InventoryCategory(models.Model):
    """Jihozlar kategoriyasi"""
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Ikonka")

    class Meta:
        verbose_name = "Jihoz kategoriyasi"
        verbose_name_plural = "Jihoz kategoriyalari"
        ordering = ['name']

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Jihoz turi"""

    class Condition(models.TextChoices):
        NEW = 'new', 'Yangi'
        GOOD = 'good', 'Yaxshi'
        FAIR = 'fair', 'O\'rtacha'
        POOR = 'poor', 'Yomon'
        BROKEN = 'broken', 'Buzilgan'

    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items',
        verbose_name="Kategoriya"
    )
    name = models.CharField(max_length=100, verbose_name="Nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    image = models.ImageField(
        upload_to='inventory/',
        blank=True,
        null=True,
        verbose_name="Rasm"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Narxi"
    )

    class Meta:
        verbose_name = "Jihoz turi"
        verbose_name_plural = "Jihoz turlari"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category.name if self.category else ''} - {self.name}"


class InventoryItemImage(models.Model):
    """Jihoz rasmlari (ko'p rasm)"""
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Jihoz"
    )
    image = models.ImageField(
        upload_to='inventory/',
        verbose_name="Rasm"
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name="Izoh")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        verbose_name = "Jihoz rasmi"
        verbose_name_plural = "Jihoz rasmlari"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.item.name} - rasm #{self.order}"


class RoomInventory(models.Model):
    """Xonadagi jihozlar"""

    class Condition(models.TextChoices):
        NEW = 'new', 'Yangi'
        GOOD = 'good', 'Yaxshi'
        FAIR = 'fair', 'O\'rtacha'
        POOR = 'poor', 'Yomon'
        BROKEN = 'broken', 'Buzilgan'

    room = models.ForeignKey(
        'buildings.Room',
        on_delete=models.CASCADE,
        related_name='inventory',
        verbose_name="Xona"
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='room_items',
        verbose_name="Jihoz"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
        verbose_name="Holati"
    )
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Seriya raqami")
    purchase_date = models.DateField(null=True, blank=True, verbose_name="Sotib olingan sana")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xona jihozi"
        verbose_name_plural = "Xona jihozlari"
        ordering = ['room', 'item__category', 'item__name']

    def __str__(self):
        return f"{self.room} - {self.item.name} ({self.quantity})"

    @property
    def total_value(self):
        return self.quantity * self.item.unit_price


class InventoryLog(models.Model):
    """Jihozlar harakati tarixi"""

    class Action(models.TextChoices):
        ADDED = 'added', 'Qo\'shildi'
        REMOVED = 'removed', 'Olib tashlandi'
        TRANSFERRED = 'transferred', 'Ko\'chirildi'
        REPAIRED = 'repaired', 'Ta\'mirlandi'
        REPLACED = 'replaced', 'Almashtirildi'
        CONDITION_CHANGED = 'condition', 'Holati o\'zgardi'

    room_inventory = models.ForeignKey(
        RoomInventory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs',
        verbose_name="Xona jihozi"
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name="Harakat"
    )
    old_value = models.CharField(max_length=255, blank=True, verbose_name="Eski qiymat")
    new_value = models.CharField(max_length=255, blank=True, verbose_name="Yangi qiymat")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    performed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Kim tomonidan"
    )
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name="Vaqti")

    class Meta:
        verbose_name = "Jihoz harakati"
        verbose_name_plural = "Jihozlar harakati"
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.room_inventory} - {self.get_action_display()}"