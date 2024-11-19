from django.contrib import admin
from .models import Supplier, SupplierOrder, SupplierOrderedItem


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by']
    
    @admin.display(ordering='created_by__username', description='Created By')
    def created_by(self, obj):
        return obj.created_by.username


class SupplierOrderedItemAdmin(admin.ModelAdmin):
    list_display = ['order_reference_id',
                    'supplier_name',
                    'item_name',
                    'ordered_quantity',
                    'ordered_price']

    @admin.display(ordering='order__reference_id', description='Order Reference ID')
    def order_reference_id(self, obj):
        return obj.order.reference_id

    @admin.display(ordering='order__supplier__name', description='Supplier')
    def supplier_name(self, obj):
        return obj.order.supplier.name

    @admin.display(ordering='item__name', description='Item Name')
    def item_name(self, obj):
        return obj.item.name


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierOrder)
admin.site.register(SupplierOrderedItem, SupplierOrderedItemAdmin)
