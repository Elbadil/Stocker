from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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


class GetSupplierOrdersData(generics.GenericAPIView):
    """Returns necessary data related to user's supplier orders"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        suppliers = Supplier.objects.filter(created_by=user)\
                                    .values_list('name', flat=True)
        orders_count = SupplierOrder.objects.filter(created_by=user).count()

        return Response({'suppliers': {
                            'count': suppliers.count(),
                            'names': suppliers
                        },
                        'orders_count': orders_count},
                        status=status.HTTP_200_OK)
