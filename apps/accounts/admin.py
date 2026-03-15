from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. Ro'yxatda ko'rinadigan ustunlar
    list_display = ('username', 'full_name_display', 'role', 'building', 'phone', 'avatar_thumbnail', 'is_active', 'is_staff')

    # 2. Bosganda tahrirlashga kiradigan ustunlar
    list_display_links = ('username', 'full_name_display')

    # 3. O'ng tomondagi filtrlar
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')

    # 4. Qidiruv maydonlari (ism, telefon, username bo'yicha)
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'email')

    # 5. Tahrirlash oynasidagi maydonlar guruhlanishi
    fieldsets = UserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {
            'fields': ('role', 'building', 'phone', 'avatar'),
        }),
    )

    # 6. Yangi foydalanuvchi qo'shish oynasidagi maydonlar
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'role', 'building', 'phone'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.building_id:
            from django.db.models import Q
            qs = qs.filter(
                Q(building_id=request.user.building_id) | Q(id=request.user.id)
            )
        return qs

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            # Superuser bo'lmasa building, is_superuser, is_staff, permissions ko'rinmasin
            new_fieldsets = []
            for title, opts in fieldsets:
                fields = list(opts.get('fields', []))
                for remove_field in ('building', 'is_superuser', 'user_permissions', 'groups'):
                    if remove_field in fields:
                        fields.remove(remove_field)
                new_fieldsets.append((title, {**opts, 'fields': fields}))
            return new_fieldsets
        return fieldsets

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