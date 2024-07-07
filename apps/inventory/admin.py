from django.contrib import admin
from .models import Product, Category, Supplier, AddAttr, AddAttrDescription, Post, PostDescription


admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(AddAttr)
admin.site.register(Post)
admin.site.register(AddAttrDescription)
admin.site.register(PostDescription)