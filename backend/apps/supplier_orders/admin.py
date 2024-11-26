from django.contrib import admin
from .models import Supplier, SupplierOrder, SupplierOrderedItem


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'total_orders']


class SupplierOrderedItemAdmin(admin.ModelAdmin):
    list_display = ['order_reference_id',
                    'supplier_name',
                    'item_name',
                    'ordered_quantity',
                    'ordered_price',
                    'in_inventory']

    @admin.display(ordering='order__reference_id', description='Order Reference ID')
    def order_reference_id(self, obj):
        return obj.order.reference_id

    @admin.display(ordering='order__supplier__name', description='Supplier')
    def supplier_name(self, obj):
        return obj.order.supplier.name

    @admin.display(ordering='item__name', description='Item Name')
    def item_name(self, obj):
        return obj.item.name

    @admin.display(ordering='item__in_inventory', description='In Inventory')
    def in_inventory(self, obj):
        return obj.item.in_inventory


class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'reference_id', 'supplier_name', 'delivery_status']

    @admin.display(ordering='supplier__name', description='Supplier')
    def supplier_name(self, obj):
        return obj.supplier.name


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierOrder, SupplierOrderAdmin)
admin.site.register(SupplierOrderedItem, SupplierOrderedItemAdmin)
