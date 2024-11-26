from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import CharField
from django.db.models.functions import Cast
from utils.tokens import Token
from utils.views import CreatedByUserMixin
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Supplier, SupplierOrder


class CreateListSupplier(CreatedByUserMixin,
                         generics.ListCreateAPIView):
    """Handles Supplier Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierSerializer
    queryset = Supplier.objects.all()


class GetUpdateDeleteSupplier(CreatedByUserMixin,
                              generics.RetrieveUpdateDestroyAPIView):
    """Handles Supplier Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierSerializer
    queryset = Supplier.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        supplier = self.get_object()
        if supplier.total_orders > 0:
            return Response(
                {
                    'error': f'Supplier {supplier.name} is linked to existing orders. '
                              'Manage orders before deletion.'
                },
                status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)


class BulkDeleteSupplier(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Supplier Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Supplier.objects.all()

    def destroy(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Validate ids
        invalid_uuids = Token.validate_uuids(ids)
        if invalid_uuids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all provided IDs are not valid UUIDs.',
                        'invalid_uuids': invalid_uuids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        supplier_ids = set(
            self.get_queryset()
            .filter(id__in=ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(ids) - supplier_ids
        if missing_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all suppliers could not be found.',
                        'missing_ids': list(missing_ids)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Handle suppliers with orders and without orders deletion
        suppliers_with_orders = (
            self.get_queryset()
            .filter(
                id__in=ids,
                orders__isnull=False)
            .values('id', 'name')
            .distinct()
        )
        suppliers_without_orders = (
            self.get_queryset()
            .filter(
                id__in=ids,
                orders__isnull=True)
        )
        # Case 1: All suppliers are linked to orders
        if suppliers_with_orders.exists() and not suppliers_without_orders.exists():
            return Response(
                {
                    'error': {
                        'message': 'All selected suppliers are linked to '
                                   'existing orders. Manage orders before deletion.',
                        'linked_suppliers': suppliers_with_orders,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Case 2: both suppliers with orders and without orders exist
        if suppliers_with_orders.exists() and suppliers_without_orders.exists():
            delete_count, _ = suppliers_without_orders.delete()
            suppliers_with_orders_count = suppliers_with_orders.count()
            supplier_text = "suppliers" if delete_count > 1 else "supplier"
            linked_supplier_text = "suppliers" if suppliers_with_orders_count > 1 else "supplier"
            return Response(
                {
                    'message': f'{delete_count} {supplier_text} deleted successfully, '
                               f'but {suppliers_with_orders_count} {linked_supplier_text} '
                               f'could not be deleted because they are linked '
                                'to existing orders.',
                    'linked_suppliers': suppliers_with_orders
                },
                status=status.HTTP_207_MULTI_STATUS
            )
        # Case 3: All suppliers are not linked to orders
        delete_count, _ = suppliers_without_orders.delete()
        return Response({'message': f'{delete_count} suppliers successfully deleted.'},
                         status=status.HTTP_200_OK)


class CreateListSupplierOrder(CreatedByUserMixin,
                              generics.ListCreateAPIView):
    """Handles Supplier Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderSerializer
    queryset = SupplierOrder.objects.all()


class GetUpdateDeleteSupplierOrder(CreatedByUserMixin,
                                   generics.RetrieveUpdateDestroyAPIView):
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
