from django.contrib import admin
from .models import Sale, SoldItem


class SaleAdmin(admin.ModelAdmin):
    list_display = ['id',
                    'reference_id',
                    'client_name',
                    'delivery_status',
                    'payment_status',
                    'from_order',
                    'linked_order']
    
    @admin.display(ordering='client__name', description='Client')
    def client_name(self, obj):
        return obj.client.name


class SoldItemAdmin(admin.ModelAdmin):
    list_display = ['id',
                    'order_ref_id',
                    'client_name',
                    'item_name',
                    'sold_quantity',
                    'sold_price']

    @admin.display(ordering='order__reference_id', description='Ref')
    def order_ref_id(self, obj):
        return obj.sale.reference_id

    @admin.display(ordering='order__client__name', description='Client')
    def client_name(self, obj):
        return obj.sale.client.name

    @admin.display(ordering='item__name', description='Item')
    def item_name(self, obj):
        return obj.item.name


admin.site.register(Sale, SaleAdmin)
admin.site.register(SoldItem, SoldItemAdmin)
