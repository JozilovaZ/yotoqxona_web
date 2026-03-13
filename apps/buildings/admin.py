from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Building, Floor, Room

# --- INLINES (Ichma-ich tahrirlash uchun) ---

class RoomInline(admin.TabularInline):
    """Etaj ichida xonalarni ko'rsatish"""
    model = Room
    extra = 0  # Bo'sh qatorlar soni
    fields = ('number', 'room_type', 'capacity', 'monthly_price', 'status', 'is_active')
    show_change_link = True  # Xona ichiga kirish uchun link


class FloorInline(admin.TabularInline):
    """Bino ichida etajlarni ko'rsatish"""
    model = Floor
    extra = 0
    fields = ('number', 'description', 'is_active')
    show_change_link = True


# --- ADMIN CLASSES ---

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'street', 'count_floors', 'count_rooms', 'total_capacity_display', 'is_active')
    list_filter = ('is_active', 'city')
    search_fields = ('name', 'address', 'city', 'street')
    inlines = [FloorInline]  # Binoni ochganda ichida etajlar chiqadi

    # Hisoblangan maydonlar (Optimization uchun annotation ishlatamiz)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            floors_count=Count('floors', distinct=True)
        )

    def count_floors(self, obj):
        return obj.floors_count

    count_floors.short_description = "Etajlar soni"

    def count_rooms(self, obj):
        return obj.total_rooms

    count_rooms.short_description = "Xonalar soni"

    def total_capacity_display(self, obj):
        return obj.total_capacity

    total_capacity_display.short_description = "Jami sig'im"


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'building', 'count_rooms', 'empty_rooms_count', 'is_active')
    list_filter = ('building', 'is_active')
    ordering = ('building', 'number')
    inlines = [RoomInline]  # Etajni ochganda ichida xonalar chiqadi

    def full_name(self, obj):
        return str(obj)

    full_name.short_description = "Etaj nomi"

    def count_rooms(self, obj):
        return obj.total_rooms

    count_rooms.short_description = "Xonalar"

    def empty_rooms_count(self, obj):
        return obj.empty_rooms

    empty_rooms_count.short_description = "Bo'sh xonalar"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor_info', 'room_type', 'monthly_price', 'capacity_info', 'status',
                    'occupancy_bar')
    list_display_links = ('number',)
    list_filter = ('floor__building', 'floor', 'room_type', 'status', 'is_active')
    search_fields = ('number', 'floor__building__name')
    list_editable = ('status', 'monthly_price')  # Ro'yxatdan turib narx va statusni o'zgartirish

    fieldsets = (
        ("Joylashuv", {
            'fields': ('floor', 'number')
        }),
        ("Ma'lumotlar", {
            'fields': ('room_type', 'capacity', 'monthly_price', 'description')
        }),
        ("Holat", {
            'fields': ('status', 'is_active')
        }),
    )

    def floor_info(self, obj):
        return f"{obj.floor.building.name} | {obj.floor.number}-etaj"

    floor_info.short_description = "Bino va Etaj"

    def capacity_info(self, obj):
        return f"{obj.current_occupancy} / {obj.capacity}"

    capacity_info.short_description = "Bandlik"

    # Vizual progress bar (Bandlik foizi)
    def occupancy_bar(self, obj):
        percent = obj.occupancy_percentage
        if percent >= 100:
            color = "#d32f2f"  # Qizil
        elif percent >= 50:
            color = "#f57c00"  # Zarg'aldoq
        else:
            color = "#388e3c"  # Yashil

        return format_html(
            '''
            <div style="width: 100px; background: #e0e0e0; border-radius: 4px; overflow: hidden;">
                <div style="width: {}%; background: {}; height: 16px; text-align: center; color: white; font-size: 10px; line-height: 16px;">
                </div>
            </div>
            <span style="font-size: 11px;">{}%</span>
            ''',
            percent,
            color,
            percent
        )

    occupancy_bar.short_description = "To'lish foizi"

