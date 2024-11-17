from django.contrib import admin
from .models import Item, Category, Variant, VariantOption


admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Variant)
admin.site.register(VariantOption)
