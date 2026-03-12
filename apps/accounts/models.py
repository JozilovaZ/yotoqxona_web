from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model for the dormitory system"""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        MANAGER = 'manager', 'Menejer'
        STAFF = 'staff', 'Xodim'
        RESIDENT = 'resident', 'Yashayotgan talaba'
        APPLICANT = 'applicant', 'Ariza beruvchi'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
        verbose_name="Rol"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Rasm")

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.get_full_name() or self.username}"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser

    @property
    def is_staff_member(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.STAFF] or self.is_superuser

    @property
    def is_resident(self):
        return self.role == self.Role.RESIDENT

    @property
    def is_applicant(self):
        return self.role == self.Role.APPLICANT