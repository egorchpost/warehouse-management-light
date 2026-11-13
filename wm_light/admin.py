from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from wm_light.models import (
    ItemCategory,
    StockBalance,
    StockItem,
    StockMovement,
    UnitOfMeasure,
    Warehouse,
    WarehouseClerk,
)


@admin.register(WarehouseClerk)
class WarehouseClerkAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("phone_number",)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("phone_number",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("first_name", "last_name", "phone_number")}),
    )


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name")
    search_fields = ("name", "full_name")


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_of_measure", "get_categories_display")
    list_filter = ("categories",)
    search_fields = ("name",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "warehouse_clerk")


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    """Balances are maintained automatically: read only in the admin."""

    list_display = ("warehouse", "stock_item", "quantity")
    list_filter = ("warehouse",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_date",
        "movement_type",
        "warehouse",
        "stock_item",
        "quantity",
        "quantity_for_balance",
    )
    list_filter = ("movement_type", "warehouse")
    readonly_fields = ("quantity_for_balance",)
