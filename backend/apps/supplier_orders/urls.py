from django.urls import path
from . import views


urlpatterns = [
    path('suppliers/',
        views.CreateListSupplier.as_view(),
        name='create_list_suppliers'),
    path('suppliers/<str:id>/',
        views.GetUpdateDeleteSupplier.as_view(),
        name='get_update_delete_supplier'),
    path('orders/',
        views.CreateListSupplierOrder.as_view(),
        name='create_list_supplier_order'),
    path('orders/<str:id>/',
        views.GetUpdateDeleteSupplierOrder.as_view(),
        name='get_update_delete_supplier_order'),
]