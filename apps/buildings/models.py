from django.db import models
from django.core.validators import MinValueValidator




class Building(models.Model):
    """Yotoqxona binosi"""
    name = models.CharField(max_length=100, verbose_name="Bino nomi")
    address = models.TextField(blank=True, verbose_name="Manzil")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bino"
        verbose_name_plural = "Binolar"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_floors(self):
        return self.floors.count()

    @property
    def total_rooms(self):
        return Room.objects.filter(floor__building=self).count()

    @property
    def total_capacity(self):
        return Room.objects.filter(floor__building=self).aggregate(
            total=models.Sum('capacity')
        )['total'] or 0

    @property
    def occupied_beds(self):
        from students.models import Student
        return Student.objects.filter(
            room__floor__building=self,
            is_active=True
        ).count()


class Floor(models.Model):
    """Etaj"""
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='floors',
        verbose_name="Bino"
    )
    number = models.PositiveIntegerField(verbose_name="Etaj raqami")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Etaj"
        verbose_name_plural = "Etajlar"
        ordering = ['building', 'number']
        unique_together = ['building', 'number']

    def __str__(self):
        return f"{self.building.name} - {self.number}-etaj"

    @property
    def total_rooms(self):
        return self.rooms.count()

    @property
    def empty_rooms(self):
        # Biz Python orqali sanaymiz (bu xatosiz ishlaydi)
        return sum(1 for room in self.rooms.all() if room.current_occupancy == 0)

    @property
    def total_capacity(self):
        return self.rooms.aggregate(total=models.Sum('capacity'))['total'] or 0

    @property
    def occupied_beds(self):
        from students.models import Student
        return Student.objects.filter(room__floor=self, is_active=True).count()


class Room(models.Model):
    """Xona"""

    class RoomType(models.TextChoices):
        STANDARD = 'standard', 'Standart'
        COMFORT = 'comfort', 'Komfort'
        LUX = 'lux', 'Lyuks'

    class RoomStatus(models.TextChoices):
        AVAILABLE = 'available', 'Bo\'sh'
        PARTIAL = 'partial', 'Qisman to\'lgan'
        FULL = 'full', 'To\'liq band'
        MAINTENANCE = 'maintenance', 'Ta\'mirda'

    floor = models.ForeignKey(
        Floor,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name="Etaj"
    )
    number = models.CharField(max_length=10, verbose_name="Xona raqami")
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.STANDARD,
        verbose_name="Xona turi"
    )
    capacity = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1)],
        verbose_name="Sig'imi (joy soni)"
    )
    monthly_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Oylik to'lov"
    )
    status = models.CharField(
        max_length=20,
        choices=RoomStatus.choices,
        default=RoomStatus.AVAILABLE,
        verbose_name="Holati"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xona"
        verbose_name_plural = "Xonalar"
        ordering = ['floor__building', 'floor__number', 'number']
        unique_together = ['floor', 'number']

    def __str__(self):
        return f"{self.floor.building.name} - {self.floor.number}-etaj - {self.number}-xona"

    @property
    def full_number(self):
        return f"{self.floor.number}{self.number}"

    @property
    def current_occupancy(self):
        from students.models import Student
        return Student.objects.filter(room=self, is_active=True).count()

    @property
    def available_beds(self):
        return max(0, self.capacity - self.current_occupancy)

    @property
    def occupancy_percentage(self):
        if self.capacity == 0:
            return 0
        return round((self.current_occupancy / self.capacity) * 100, 1)

    def update_status(self):
        """Xona holatini yangilash"""
        if self.status == self.RoomStatus.MAINTENANCE:
            return

        occupancy = self.current_occupancy
        if occupancy == 0:
            self.status = self.RoomStatus.AVAILABLE
        elif occupancy < self.capacity:
            self.status = self.RoomStatus.PARTIAL
        else:
            self.status = self.RoomStatus.FULL
        self.save(update_fields=['status'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)