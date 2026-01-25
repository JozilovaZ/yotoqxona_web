from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. Ro'yxatda ko'rinadigan ustunlar
    list_display = ('username', 'full_name_display', 'role', 'phone', 'avatar_thumbnail', 'is_active', 'is_staff')

    # 2. Bosganda tahrirlashga kiradigan ustunlar
    list_display_links = ('username', 'full_name_display')

    # 3. O'ng tomondagi filtrlar
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')

    # 4. Qidiruv maydonlari (ism, telefon, username bo'yicha)
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'email')

    # 5. Tahrirlash oynasidagi maydonlar guruhlanishi
    # UserAdmin.fieldsets ni olib, unga o'zimizning maydonlarni qo'shamiz
    fieldsets = UserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {
            'fields': ('role', 'phone', 'avatar'),
        }),
    )

    # 6. Yangi foydalanuvchi qo'shish oynasidagi maydonlar
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'role', 'phone'),
        }),
    )

    # --- Qo'shimcha metodlar ---

    # To'liq ismni chiroyli ko'rsatish
    def full_name_display(self, obj):
        return obj.get_full_name() or obj.username

    full_name_display.short_description = "F.I.SH"

    # Rasmni kichkina qilib ko'rsatish
    def avatar_thumbnail(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                               obj.avatar.url)
        return "Rasm yo'q"

    avatar_thumbnail.short_description = "Avatar"


# Agar kelajakda admin panel sarlavhasini o'zgartirmoqchi bo'lsangiz:
admin.site.site_header = "Yotoqxona Boshqaruv Tizimi"
admin.site.site_title = "Yotoqxona Admin"
admin.site.index_title = "Boshqaruv Paneli"