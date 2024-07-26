from django.urls import path
from . import views


urlpatterns = [
    path('', views.listItems, name='inventory_home'),
    path('add_item/', views.addItem, name='add_item'),
    path('edit_item/<str:product_id>/', views.editItem, name='edit_item'),
    path('delete_item/<str:product_id>/', views.deleteItem, name='delete_item'),
    path('add_category/', views.addCategory, name="add_category"),
    path('add_supplier/', views.addSupplier, name="add_supplier"),
    path('category_items/<str:category_name>', views.itemsByCategory, name="category_items"),
    path('supplier_items/<str:supplier_name>', views.itemsBySupplier, name="supplier_items")
]