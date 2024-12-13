from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from utils.views import CreatedByUserMixin
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Sale, SoldItem


class CreateListSale(CreatedByUserMixin, generics.ListCreateAPIView):
    """Handles Sale Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SaleSerializer
    queryset = Sale.objects.all()


class GetUpdateDeleteSale(CreatedByUserMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    """Handles Sale Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SaleSerializer
    queryset = Sale.objects.all()
    lookup_field = 'id'


class CreateListSoldItem(CreatedByUserMixin,
                         generics.ListCreateAPIView):
    """Handles Sold Item Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SoldItemSerializer
    queryset = SoldItem.objects.all()


class GetUpdateDeleteSoldItem(CreatedByUserMixin,
                              generics.RetrieveUpdateDestroyAPIView):
    """Handles Sold Item Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SoldItemSerializer
    queryset = SoldItem.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        sold_item = self.get_object()

        # Reset item's inventory quantity
        if not sold_item.sale.from_order:
            sold_item.item.quantity += sold_item.sold_quantity
            sold_item.item.save()

        return super().delete(request, *args, **kwargs)
