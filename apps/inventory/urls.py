from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='inventory_home')
]