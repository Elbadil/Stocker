from django.urls import path
from . import views


urlpatterns = [
    path('items/<str:user_id>/', views.userItems),
    path('category_items/<str:category_id>/', views.categoryItems),
    path('supplier_items/<str:supplier_id>/', views.supplierItems)
]
