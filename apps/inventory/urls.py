from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='inventory_home'),
    path('add_item/', views.addItem, name='add_item')
]