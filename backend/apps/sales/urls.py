from django.urls import path
from . import views


urlpatterns = [
    # Sales
    path('',
         views.CreateListSales.as_view(),
         name='create_list_sales'),
    path('bulk_delete/',
         views.BulkDeleteSales.as_view(),
         name='bulk_delete_sales'),
    path('<uuid:id>/',
         views.GetUpdateDeleteSales.as_view(),
         name='get_update_delete_sales'),
    
    # Sold Items
    path('<uuid:sale_id>/items/',
         views.CreateListSoldItems.as_view(),
         name='create_list_sold_items'),
    path('<uuid:sale_id>/items/<uuid:id>/',
         views.GetUpdateDeleteSoldItems.as_view(),
         name='get_update_delete_sold_items'),
]