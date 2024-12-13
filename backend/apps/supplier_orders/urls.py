from django.urls import path
from . import views


urlpatterns = [
    # Suppliers
    path('suppliers/',
        views.CreateListSuppliers.as_view(),
        name='create_list_suppliers'),
    path('suppliers/bulk_delete/',
        views.BulkDeleteSuppliers.as_view(),
        name='bulk_delete_suppliers'),
    path('suppliers/<str:id>/',
        views.GetUpdateDeleteSuppliers.as_view(),
        name='get_update_delete_suppliers'),

    # Supplier Orders
    path('orders/',
        views.CreateListSupplierOrders.as_view(),
        name='create_list_supplier_orders'),
    path('orders/bulk_delete/',
        views.BulkDeleteSupplierOrders.as_view(),
        name='bulk_delete_supplier_orders'),
    path('orders/<str:id>/',
        views.GetUpdateDeleteSupplierOrders.as_view(),
        name='get_update_delete_supplier_orders'),
    
    # Supplier Ordered Items
    path('ordered_items/',
        views.CreateListSupplierOrderedItems.as_view(),
        name='create_list_supplier_ordered_items'),
    path('ordered_items/<str:id>/',
        views.GetUpdateDeleteSupplierOrderedItems.as_view(),
        name='get_update_delete_supplier_ordered_items'),

    # Supplier Orders Data
    path('data/',
         views.GetSupplierOrdersData.as_view(),
         name='get_supplier_orders_data')
]