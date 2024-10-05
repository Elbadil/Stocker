from django.urls import path
from . import views


urlpatterns = [
    path('items/<str:id>/',
         views.GetUpdateDeleteItem.as_view(),
         name='get_update_delete_item'),
    path('items/', views.CreateItem.as_view(),
         name='create_item'),
    path('user/items/', views.ListUserItems.as_view(),
         name='list_user_items'),
    path('data/', views.GetUserInventoryData.as_view(),
         name='inventory_data'),
    path('categories/<str:id>/',
         views.GetUpdateDeleteCategory.as_view(),
         name='get_update_delete_category'),
]
