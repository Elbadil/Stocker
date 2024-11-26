from django.contrib import admin
from .models import Item, Category, Variant, VariantOption


class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'quantity',
        'price',
        'total_client_orders',
        'total_supplier_orders',
        'in_inventory',
        'created_by'
    ]

    @admin.display(description='Client Orders')
    def total_client_orders(self, obj):
        return obj.total_client_orders

    @admin.display(description='Supplier Orders')
    def total_supplier_orders(self, obj):
        return obj.total_supplier_orders

    @admin.display(ordering='created_by__username', description='Created By')
    def created_by(self, obj):
        return obj.created_by.username


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by']

    @admin.display(ordering='created_by__username', description='Created By')
    def created_by(self, obj):
        return obj.created_by.username


admin.site.register(Item, ItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Variant)
admin.site.register(VariantOption)
