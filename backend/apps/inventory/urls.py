from django.urls import path
from . import views


urlpatterns = [
    # Items
    path('items/',
         views.CreateListItems.as_view(),
         name='create_list_items'),
    path('items/bulk_delete/',
         views.BulkDeleteItems.as_view(),
         name='bulk_delete_items'),
    path('items/<str:id>/',
         views.GetUpdateDeleteItems.as_view(),
         name='get_update_delete_items'),

    # Inventory data
    path('data/',
         views.GetInventoryData.as_view(),
         name='get_inventory_data'),
]
