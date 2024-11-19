from django.contrib import admin
from . import models


class ClientOrderedItemAdmin(admin.ModelAdmin):
    list_display = ['order_reference_id',
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


admin.site.register(models.Location)
admin.site.register(models.Client)
admin.site.register(models.AcquisitionSource)
admin.site.register(models.OrderStatus)
admin.site.register(models.ClientOrder)
admin.site.register(models.ClientOrderedItem, ClientOrderedItemAdmin)
admin.site.register(models.Country)
admin.site.register(models.City)
