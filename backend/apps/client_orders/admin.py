from django.contrib import admin
from . import models


class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'total_orders']

class ClientOrderedItemAdmin(admin.ModelAdmin):
    list_display = ['id',
                    'order_reference_id',
                    'client_name',
                    'item_name',
                    'ordered_quantity',
                    'ordered_price']

    @admin.display(ordering='order__reference_id', description='Order Reference ID')
    def order_reference_id(self, obj):
        return obj.order.reference_id
    
    @admin.display(ordering='order__supplier__name', description='Client')
    def client_name(self, obj):
        return obj.order.client.name

    @admin.display(ordering='item__name', description='Item Name')
    def item_name(self, obj):
        return obj.item.name

class ClientOrderAdmin(admin.ModelAdmin):
    list_display = ['id',
                    'reference_id',
                    'client_name',
                    'delivery_status',
                    'payment_status',
                    'linked_sale']

    @admin.display(ordering='client__name', description='Client')
    def client_name(self, obj):
        return obj.client.name



admin.site.register(models.Location)
admin.site.register(models.Client, ClientAdmin)
admin.site.register(models.AcquisitionSource)
admin.site.register(models.OrderStatus)
admin.site.register(models.ClientOrder, ClientOrderAdmin)
admin.site.register(models.ClientOrderedItem, ClientOrderedItemAdmin)
admin.site.register(models.Country)
admin.site.register(models.City)
