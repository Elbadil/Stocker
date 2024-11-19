from django.urls import path
from . import views


urlpatterns = [
    path('suppliers/',
        views.CreateListSupplier.as_view(),
        name='create_list_suppliers'),
    path('suppliers/<str:id>/',
        views.GetUpdateDeleteSupplier.as_view(),
        name='get_update_delete_supplier'),
]