from django.urls import path
from . import views

urlpatterns =[
    path('clients/',
         views.CreateListClient.as_view(),
         name='create_list_client'),
    path('client/<str:id>/',
         views.GetUpdateDeleteClient.as_view(),
         name='get_update_delete_client'),
    path('orders/',
         views.CreateListOrder.as_view(),
         name="create_list_order"),
    path('order/<str:id>/',
         views.GetUpdateDeleteOrder.as_view(),
         name="get_update_delete_order")
]