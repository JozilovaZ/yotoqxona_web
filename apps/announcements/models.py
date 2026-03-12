from django.db import models
from django.conf import settings


class Announcement(models.Model):
    """Ichki e'lonlar va xabarlar"""

    class Category(models.TextChoices):
        WATER = 'water', "Suv ta'minoti"
        ELECTRICITY = 'electricity', "Elektr energiyasi"
        GAS = 'gas', "Gaz ta'minoti"
        INTERNET = 'internet', 'Internet'
        MAINTENANCE = 'maintenance', "Ta'mirlash ishlari"
        RULES = 'rules', 'Qoidalar'
        EVENT = 'event', 'Tadbir'
        GENERAL = 'general', 'Umumiy'
        URGENT = 'urgent', 'Shoshilinch'

    class Priority(models.TextChoices):
        LOW = 'low', 'Past'
        NORMAL = 'normal', "O'rta"
        HIGH = 'high', 'Yuqori'
        CRITICAL = 'critical', 'Juda muhim'

    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    content = models.TextField(verbose_name="Mazmuni")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
        verbose_name="Kategoriya"
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        verbose_name="Muhimlik"
    )

    # Qaysi binoga tegishli (bo'sh bo'lsa - hammaga)
    building = models.ForeignKey(
        'buildings.Building',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='announcements',
        verbose_name="Bino (bo'sh = hammaga)"
    )

    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
        verbose_name="Yaratuvchi"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Amal qilish muddati")

    class Meta:
        verbose_name = "E'lon"
        verbose_name_plural = "E'lonlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"

    @property
    def category_icon(self):
        icons = {
            'water': 'fa-droplet',
            'electricity': 'fa-bolt',
            'gas': 'fa-fire',
            'internet': 'fa-wifi',
            'maintenance': 'fa-wrench',
            'rules': 'fa-book',
            'event': 'fa-calendar',
            'general': 'fa-bullhorn',
            'urgent': 'fa-triangle-exclamation',
        }
        return icons.get(self.category, 'fa-bullhorn')

    @property
    def priority_color(self):
        colors = {
            'low': '#6c757d',
            'normal': '#7000FF',
            'high': '#fd7e14',
            'critical': '#dc3545',
        }
        return colors.get(self.priority, '#7000FF')
