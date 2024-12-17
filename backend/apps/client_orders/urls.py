from django.urls import path
from . import views

urlpatterns =[
    # Clients
    path('clients/',
         views.CreateListClients.as_view(),
         name='create_list_clients'),
    path('clients/bulk_delete/',
         views.BulkDeleteClients.as_view(),
         name='bulk_delete_clients'),
    path('clients/<uuid:id>/',
         views.GetUpdateDeleteClients.as_view(),
         name='get_update_delete_clients'),

    # Client Orders
    path('',
         views.CreateListClientOrders.as_view(),
         name="create_list_client_orders"),
    path('bulk_delete/',
         views.BulkDeleteClientOrders.as_view(),
         name='bulk_delete_client_orders'),
    path('<uuid:id>/',
         views.GetUpdateDeleteClientOrders.as_view(),
         name="get_update_delete_client_orders"),

    # Client Ordered Items
    path('<uuid:order_id>/items/',
         views.CreateListClientOrderedItems.as_view(),
         name="create_list_client_ordered_items"),
    path('<uuid:order_id>/items/<uuid:id>/',
         views.GetUpdateDeleteClientOrderedItems.as_view(),
         name="get_update_delete_client_ordered_items"),

    # Cities
    path('cities/',
         views.BulkCreateListCities.as_view(),
         name="bulk_create_cities"),

    # Client Orders Data
    path('data/',
         views.GetClientOrdersData.as_view(),
         name='get_client_orders_data')
]