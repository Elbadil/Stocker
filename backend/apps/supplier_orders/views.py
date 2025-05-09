from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import CharField, Q
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models.functions import Cast
from utils.tokens import Token
from utils.views import (CreatedByUserMixin,
                         validate_linked_items_for_deletion,
                         validate_deletion_for_delivered_parent_instance)
from utils.status import (DELIVERY_STATUS_OPTIONS,
                          PAYMENT_STATUS_OPTIONS,
                          COMPLETED_STATUS,
                          ACTIVE_DELIVERY_STATUS,
                          FAILED_STATUS)
from utils.activity import register_activity
from ..base.auth import TokenVersionAuthentication
from ..inventory.models import Item
from .utils import validate_supplier_order
from . import serializers
from .models import Supplier, SupplierOrder, SupplierOrderedItem


class CreateListSuppliers(CreatedByUserMixin,
                         generics.ListCreateAPIView):
    """Handles Supplier Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierSerializer
    queryset = Supplier.objects.all()


class GetUpdateDeleteSuppliers(CreatedByUserMixin,
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

        register_activity(request.user, "deleted", "supplier", [supplier.name])

        return super().destroy(request, *args, **kwargs)


class BulkDeleteSuppliers(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Supplier Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Supplier.objects.all()

    def destroy(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided.'},
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
        suppliers_for_deletion = list(
            suppliers_without_orders
            .values_list('name', flat=True)
        )
        if suppliers_with_orders.exists() and suppliers_without_orders.exists():
            delete_count, _ = suppliers_without_orders.delete()
            register_activity(request.user, "deleted", "supplier", suppliers_for_deletion)
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
        register_activity(request.user, "deleted", "supplier", suppliers_for_deletion)
        return Response({'message': f'{delete_count} suppliers successfully deleted.'},
                         status=status.HTTP_200_OK)


class CreateListSupplierOrders(CreatedByUserMixin,
                              generics.ListCreateAPIView):
    """Handles Supplier Order Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderSerializer
    queryset = SupplierOrder.objects.all()


class GetUpdateDeleteSupplierOrders(CreatedByUserMixin,
                                   generics.RetrieveUpdateDestroyAPIView):
    """Handles Supplier Order Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderSerializer
    queryset = SupplierOrder.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()

        register_activity(
            request.user,
            "deleted",
            "supplier order",
            [order.reference_id]
        )

        return super().destroy(request, *args, **kwargs)


class BulkDeleteSupplierOrders(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Supplier Order Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = SupplierOrder.objects.all()

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Validate ids
        invalid_ids = Token.validate_uuids(ids)
        if invalid_ids:
            return Response(
                {
                    'error' : {
                        'message': 'Some or all provided IDs are not valid uuids.',
                        'invalid_ids': invalid_ids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders_ids = set(
            self.get_queryset()
            .filter(id__in=ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(ids) - orders_ids
        if missing_ids:
            return Response(
                {
                    'error' : {
                        'message': 'Some or all selected orders could not be found.',
                        'missing_ids': list(missing_ids)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Delete selected orders
        orders_for_deletion = SupplierOrder.objects.filter(id__in=ids)
        orders_for_deletion_ref_ids = list(
            orders_for_deletion
            .values_list('reference_id', flat=True)
        )
        orders_for_deletion_count = orders_for_deletion.count()
        orders_for_deletion.delete()

        register_activity(
            request.user,
            "deleted",
            "supplier order",
            orders_for_deletion_ref_ids
        )

        return Response({'message': f'{orders_for_deletion_count} supplier orders successfully deleted.'},
                         status=status.HTTP_200_OK)
 

class CreateListSupplierOrderedItems(CreatedByUserMixin,
                                    generics.ListCreateAPIView):
    """Handles Supplier Ordered Item Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderedItemSerializer
    queryset = SupplierOrderedItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_supplier_order(order_id, self.request.user)
        return queryset.filter(order=order)
    
    def perform_create(self, serializer):
        order_id = self.kwargs['order_id']
        order = validate_supplier_order(order_id, self.request.user)
        serializer.save(order=order)


class GetUpdateDeleteSupplierOrderedItems(CreatedByUserMixin,
                                          generics.RetrieveUpdateDestroyAPIView):
    """Handles Supplier Ordered Item Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SupplierOrderedItemSerializer
    queryset = SupplierOrderedItem.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_supplier_order(order_id, self.request.user)
        return queryset.filter(order=order)

    def delete(self, request, *args, **kwargs):
        ordered_item = self.get_object()

        # Validate ordered item order delivery status
        status_validation = (
            validate_deletion_for_delivered_parent_instance(ordered_item.order)
        )
        if isinstance(status_validation, Response):
            return status_validation

        # Validate order's ordered items records
        if len(ordered_item.order.items) == 1:
            return Response(
                {
                    'error': (
                        "This item cannot be deleted because it is the only item in the "
                        f"order with reference ID '{ordered_item.order.reference_id}'. "
                        "Every order must have at least one item."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete ordered item
        ordered_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkDeleteSupplierOrderedItems(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Supplier Ordered Items Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = SupplierOrderedItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_supplier_order(order_id, self.request.user)
        return queryset.filter(order=order)
    
    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        queryset = self.get_queryset()
        
        # Validate ids and items for deletion
        result = validate_linked_items_for_deletion(ids, queryset, SupplierOrder)

        # Return Response if validation failed
        if isinstance(result, Response):
            return result

        # Validate ordered items order delivery status
        order = queryset.first().order
        status_validation = validate_deletion_for_delivered_parent_instance(order)
        if isinstance(status_validation, Response):
            return status_validation

        # Perform items deletion
        order, items_for_deletion = result
        delete_count, _ = items_for_deletion.delete()
        return Response({'message': f'{delete_count} ordered items successfully deleted.'},
                         status=status.HTTP_200_OK)


class GetSupplierOrdersData(generics.GenericAPIView):
    """Returns necessary data related to user's supplier orders"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        # Supplier with their linked items
        suppliers = (
            Supplier.objects
            .filter(created_by=user)
            .annotate(
                item_names=ArrayAgg(
                    'items__name',
                    filter=Q(items__name__isnull=False))
                )
            .values('name', 'item_names')
        )

        # Item without supplier
        no_supplier_items = (
            Item.objects
            .filter(
                created_by=user,
                supplier=None
            )
            .values_list('name', flat=True)
        )

        # Total supplier orders count
        orders_count = SupplierOrder.objects.filter(created_by=user).count()

        # Completed orders
        completed_orders = (
            SupplierOrder.objects
            .filter(
                created_by=user,
                delivery_status__name__in=COMPLETED_STATUS)
            .count()
        )

        # Active Orders
        active_orders = (
            SupplierOrder.objects
            .filter(
                created_by=user,
                delivery_status__name__in=ACTIVE_DELIVERY_STATUS)
            .count()
        )

        # Failed Orders
        failed_orders = (
            SupplierOrder.objects
            .filter(
                created_by=user,
                delivery_status__name__in=FAILED_STATUS)
            .count()
        )

        # Orders Status
        orders_status = {'delivery_status': DELIVERY_STATUS_OPTIONS,
                         'payment_status': PAYMENT_STATUS_OPTIONS,
                         'active': active_orders,
                         'completed': completed_orders,
                         'failed': failed_orders}

        return Response({'suppliers': suppliers,
                         'no_supplier_items': no_supplier_items,
                         'suppliers_count': suppliers.count(),
                         'orders_count': orders_count,
                         'order_status': orders_status},
                         status=status.HTTP_200_OK)
