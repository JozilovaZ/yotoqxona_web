from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import InventoryCategory, InventoryItem, InventoryItemImage, RoomInventory, InventoryLog


# --- INLINES ---

class InventoryItemInline(admin.TabularInline):
    """Kategoriya ichida jihoz turlarini ko'rsatish"""
    model = InventoryItem
    extra = 0
    fields = ('name', 'image', 'unit_price')
    show_change_link = True


class InventoryItemImageInline(admin.TabularInline):
    """Jihoz ichida rasmlarni ko'rsatish (ko'p rasm)"""
    model = InventoryItemImage
    extra = 5
    fields = ('image', 'image_preview', 'caption', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:80px;height:60px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return '-'
    image_preview.short_description = "Ko'rinishi"


class InventoryLogInline(admin.TabularInline):
    """Jihoz ichida uning tarixini ko'rsatish"""
    model = InventoryLog
    extra = 0
    fields = ('action', 'old_value', 'new_value', 'performed_by', 'performed_at', 'notes')
    readonly_fields = ('performed_at', 'performed_by', 'action', 'old_value', 'new_value', 'notes')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False  # Loglarni qo'lda qo'shib bo'lmaydi


# --- ADMIN CLASSES ---

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_count', 'description')
    search_fields = ('name',)
    inlines = [InventoryItemInline]

    def item_count(self, obj):
        return obj.items.count()

    item_count.short_description = "Jihoz turlari soni"


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'category', 'images_count', 'unit_price_fmt', 'total_in_rooms')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    list_per_page = 20
    inlines = [InventoryItemImageInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return '-'
    image_preview.short_description = "Rasm"

    def images_count(self, obj):
        count = obj.images.count()
        old = 1 if obj.image else 0
        total = count + old
        return f"{total} ta rasm"
    images_count.short_description = "Rasmlar"

    def unit_price_fmt(self, obj):
        return f"{obj.unit_price:,.0f} so'm"

    unit_price_fmt.short_description = "Donasining narxi"

    def total_in_rooms(self, obj):
        count = obj.room_items.aggregate(total=Sum('quantity'))['total'] or 0
        return f"{count} dona"

    total_in_rooms.short_description = "Xonalardagi jami soni"


@admin.register(RoomInventory)
class RoomInventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'room_link', 'quantity', 'condition', 'total_value_fmt', 'purchase_date')
    list_filter = ('condition', 'item__category', 'purchase_date')
    search_fields = ('item__name', 'room__number', 'serial_number')
    autocomplete_fields = ['room', 'item']  # Room va Item ko'p bo'lsa qotmasligi uchun
    list_editable = ('condition',)  # Ro'yxatdan turib holatni o'zgartirish
    inlines = [InventoryLogInline]  # Tarixni ko'rish

    # N+1 muammosini oldini olish uchun (Optimization)
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('room', 'item', 'room__floor__building')

    def item_name(self, obj):
        return f"{obj.item.name} ({obj.serial_number})" if obj.serial_number else obj.item.name

    item_name.short_description = "Jihoz"

    def room_link(self, obj):
        return format_html(
            '<a href="/admin/buildings/room/{}/change/">{}</a>',
            obj.room.id,
            str(obj.room)
        )

    room_link.short_description = "Xona"

    def total_value_fmt(self, obj):
        return f"{obj.total_value:,.0f}"

    total_value_fmt.short_description = "Jami qiymati"

    def condition_colored(self, obj):
        colors = {
            'new': 'green',
            'good': '#2e7d32',  # Dark green
            'fair': 'orange',
            'poor': '#d32f2f',  # Red
            'broken': 'black',
        }
        icons = {
            'new': '✨',
            'good': '👍',
            'fair': '😐',
            'poor': '👎',
            'broken': '💀',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.condition, 'black'),
            icons.get(obj.condition, ''),
            obj.get_condition_display()
        )

    condition_colored.short_description = "Holati"


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('performed_at', 'room_inventory', 'action_colored', 'performed_by')
    list_filter = ('action', 'performed_at')
    search_fields = ('room_inventory__item__name', 'notes', 'performed_by__username')
    readonly_fields = ('performed_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.performed_by:
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)

    def action_colored(self, obj):
        colors = {
            'added': 'green',
            'removed': 'red',
            'transferred': 'blue',
            'repaired': 'orange',
            'replaced': 'purple',
            'condition': 'brown',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.action, 'black'),
            obj.get_action_display()
        )

    action_colored.short_description = "Harakat"