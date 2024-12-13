from django.urls import path
from . import views


urlpatterns = [
    # Sold Items
    path('sold_items/',
         views.CreateListSoldItem.as_view(),
         name='create_list_sold_items'),
    path('sold_items/<str:id>/',
         views.GetUpdateDeleteSoldItem.as_view(),
         name='get_update_delete_sold_items'),

    # Sales
    path('',
         views.CreateListSale.as_view(),
         name='create_list_sales'),
    path('<str:id>/',
         views.GetUpdateDeleteSale.as_view(),
         name='get_update_delete_sales'),
]