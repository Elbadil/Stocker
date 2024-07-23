from django.urls import path
from . import views


urlpatterns = [
    path('', views.listItems, name='inventory_home'),
    path('add_item/', views.addItem, name='add_item'),
    path('edit_item/<str:product_id>/', views.editItem, name='edit_item'),
    path('delete_item/<str:product_id>/', views.deleteItem, name='delete_item'),
    path('add_category/', views.addCategory, name="add_category")
]