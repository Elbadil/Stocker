from django.urls import path
from . import views

urlpatterns =[ 
    path('client/<str:id>/',
         views.GetUpdateDeleteClient.as_view(),
         name='get_update_delete_client'),
    path('clients/',
         views.CreateListClient.as_view(),
         name='create_list_client'),
]