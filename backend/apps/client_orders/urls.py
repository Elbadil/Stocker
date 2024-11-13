from django.urls import path
from . import views

urlpatterns =[
    path('clients/',
         views.CreateListClient.as_view(),
         name='create_list_client'),
    path('clients/bulk_delete/',
         views.BulkDeleteClients.as_view(),
         name='bulk_delete_clients'),
    path('clients/<str:id>/',
         views.GetUpdateDeleteClient.as_view(),
         name='get_update_delete_client'),
    path('orders/',
         views.CreateListClientOrder.as_view(),
         name="create_list_order"),
    path('orders/bulk_delete/',
         views.BulkDeleteClientOrders.as_view(),
         name='bulk_delete_orders'),
    path('orders/<str:id>/',
         views.GetUpdateDeleteClientOrder.as_view(),
         name="get_update_delete_order"),
    path('cities/',
         views.BulkCreateListCities.as_view(),
         name="bulk_create_cities"),
    path('data/',
         views.GetClientOrdersData.as_view(),
         name='get_client_orders_data')
]