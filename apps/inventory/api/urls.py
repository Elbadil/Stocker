from django.urls import path
from . import views


urlpatterns = [
    path('items/<str:user_id>/', views.userItems),
    path('category_items/<str:category_id>/', views.categoryItems)
]
