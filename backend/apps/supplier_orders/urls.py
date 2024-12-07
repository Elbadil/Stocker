from django.urls import path
from . import views


urlpatterns = [
    path('suppliers/',
        views.CreateListSupplier.as_view(),
        name='create_list_suppliers'),
    path('suppliers/bulk_delete/',
        views.BulkDeleteSupplier.as_view(),
        name='bulk_delete_suppliers'),
    path('suppliers/<str:id>/',
        views.GetUpdateDeleteSupplier.as_view(),
        name='get_update_delete_supplier'),
    path('orders/',
        views.CreateListSupplierOrder.as_view(),
        name='create_list_supplier_order'),
    path('orders/bulk_delete/',
        views.BulkDeleteSupplierOrders.as_view(),
        name='bulk_delete_supplier_orders'),
    path('orders/<str:id>/',
        views.GetUpdateDeleteSupplierOrder.as_view(),
        name='get_update_delete_supplier_order'),
    path('data/',
         views.GetSupplierOrdersData.as_view(),
         name='get_supplier_orders_data')
]