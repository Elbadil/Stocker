from django.contrib import admin
from . import models


admin.site.register(models.Location)
admin.site.register(models.Client)
admin.site.register(models.AcquisitionSource)
admin.site.register(models.ClientOrderStatus)
admin.site.register(models.ClientOrder)
admin.site.register(models.ClientOrderedItem)
admin.site.register(models.Country)
admin.site.register(models.City)
