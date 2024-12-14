from django.urls import path
from . import views


urlpatterns = [
    # Sold Items
    path('sold_items/',
         views.CreateListSoldItems.as_view(),
         name='create_list_sold_items'),
    path('sold_items/<str:id>/',
         views.GetUpdateDeleteSoldItems.as_view(),
         name='get_update_delete_sold_items'),

    # Sales
    path('',
         views.CreateListSales.as_view(),
         name='create_list_sales'),
    path('bulk_delete/',
         views.BulkDeleteSales.as_view(),
         name='bulk_delete_sales'),
    path('<str:id>/',
         views.GetUpdateDeleteSales.as_view(),
         name='get_update_delete_sales'),
]