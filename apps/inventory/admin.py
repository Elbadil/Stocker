from django.contrib import admin
from .models import Item, Category, Supplier, Variant, VariantOptions, Post


admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Variant)
admin.site.register(Post)
admin.site.register(VariantOptions)
