from django.urls import path
from . import views


urlpatterns = [
    path('', views.listItems, name='inventory_home'),
    path('add_item/', views.addItem, name='add_item'),
    path('edit_item/<str:product_id>/', views.editItem, name='edit_item')
]