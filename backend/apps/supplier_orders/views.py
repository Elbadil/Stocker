from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Supplier, SupplierOrder


class CreateListSupplier(generics.ListCreateAPIView):
    """Handles Supplier Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierSerializer

    def get_queryset(self):
        return Supplier.objects.filter(created_by=self.request.user)


class GetUpdateDeleteSupplier(generics.RetrieveUpdateDestroyAPIView):
    """Handles Supplier Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierSerializer
    queryset = Supplier.objects.all()
    lookup_field = 'id'


class CreateListSupplierOrder(generics.ListCreateAPIView):
    """Handles Supplier Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderSerializer

    def get_queryset(self):
        return SupplierOrder.objects.filter(created_by=self.request.user)


class GetUpdateDeleteSupplierOrder(generics.RetrieveUpdateDestroyAPIView):
    """Handles Supplier Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderSerializer
    queryset = SupplierOrder.objects.all()
    lookup_field = 'id'
