from django.contrib import admin
from . import models


admin.site.register(models.Location)
admin.site.register(models.Client)
admin.site.register(models.AcquisitionSource)
admin.site.register(models.OrderStatus)
admin.site.register(models.Order)
admin.site.register(models.OrderedItem)
admin.site.register(models.Country)
admin.site.register(models.City)
