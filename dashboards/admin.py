from django.contrib import admin
from .models import Product, Order, ActivityLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Product model in the Django admin.
    """
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_available', 'created_at')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description', 'category')
    list_editable = ('price', 'stock_quantity', 'is_available')
    ordering = ('-created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the display of the Order model in the Django admin.
    """
    list_display = ('id', 'user', 'product', 'quantity', 'total_price', 'status', 'order_type', 'created_at')
    list_filter = ('status', 'order_type', 'created_at')
    search_fields = ('user__email', 'product__name')
    autocomplete_fields = ('user', 'product')
    ordering = ('-created_at',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Provides a read-only view of the ActivityLog in the Django admin.
    """
    list_display = ('user', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'action', 'details')
    readonly_fields = ('user', 'action', 'details', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False