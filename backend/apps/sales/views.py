from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import Cast
from django.db.models import CharField
from utils.views import (CreatedByUserMixin,
                         validate_linked_items_for_deletion,
                         validate_deletion_for_delivered_parent_instance)
from utils.tokens import Token
from utils.activity import register_activity
from utils.status import (DELIVERY_STATUS_OPTIONS,
                          PAYMENT_STATUS_OPTIONS,
                          ACTIVE_DELIVERY_STATUS,
                          COMPLETED_STATUS,
                          FAILED_STATUS)
from .utils import validate_sale, reset_sold_items
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Sale, SoldItem


class CreateListSales(CreatedByUserMixin, generics.ListCreateAPIView):
    """Handles Sale Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SaleSerializer
    queryset = Sale.objects.all()


class GetUpdateDeleteSales(CreatedByUserMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    """Handles Sale Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SaleSerializer
    queryset = Sale.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        sale = self.get_object()
        # Reset sale's sold items if the sale is not from order
        if not sale.has_order:
            reset_sold_items(sale.items)
        
        register_activity(request.user, "deleted", "sale", [sale.reference_id])

        return super().delete(request, *args, **kwargs)


class BulkDeleteSales(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Sales Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Sale.objects.all()

    def delete(self, request, *args, **kwargs):
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
                        'message': 'Some or all provided IDs are not valid uuids.',
                        'invalid_uuids': invalid_uuids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sale_ids = set(
            self.get_queryset()
            .filter(id__in=ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(ids) - sale_ids
        if missing_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all selected sales are not found.',
                        'missing_ids': list(missing_ids)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # Perform sales deletion after validation
        sales_for_deletion = self.get_queryset().filter(id__in=ids)
        sales_for_deletion_ref_ids = list(
            sales_for_deletion
            .values_list('reference_id', flat=True)
        )

        delete_count = 0
        for sale in sales_for_deletion:
            if not sale.has_order:
                reset_sold_items(sale.items)
            SoldItem.objects.filter(sale=sale).delete()
            sale.delete()
            delete_count += 1

        register_activity(request.user, "deleted", "sale", sales_for_deletion_ref_ids)

        return Response({'message': f'{delete_count} sales successfully deleted.'},
                         status=status.HTTP_200_OK)


class CreateListSoldItems(CreatedByUserMixin, generics.ListCreateAPIView):
    """Handles Sold Item Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SoldItemSerializer
    queryset = SoldItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        sale_id = self.kwargs['sale_id']
        sale = validate_sale(sale_id, self.request.user)
        return queryset.filter(sale=sale)

    def perform_create(self, serializer):
        sale_id = self.kwargs['sale_id']
        sale = validate_sale(sale_id, self.request.user)
        serializer.save(sale=sale)


class GetUpdateDeleteSoldItems(CreatedByUserMixin,
                              generics.RetrieveUpdateDestroyAPIView):
    """Handles Sold Item Retrieval, Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SoldItemSerializer
    queryset = SoldItem.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        sale_id = self.kwargs['sale_id']
        sale = validate_sale(sale_id, self.request.user)
        return queryset.filter(sale=sale)

    def delete(self, request, *args, **kwargs):
        sold_item = self.get_object()

        # Validate sold item's sale delivery status
        status_validation = (
            validate_deletion_for_delivered_parent_instance(sold_item.sale)
        )
        if isinstance(status_validation, Response):
            return status_validation

        # Validate sale's sold items records
        if len(sold_item.sale.items) == 1:
            return Response(
                {
                    'error': (
                        "This item cannot be deleted because it is the only item in the "
                        f"sale record with reference ID '{sold_item.sale.reference_id}'. "
                        "Every sale record must have at least one item."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset item's inventory quantity
        sold_item.item.quantity += sold_item.sold_quantity
        sold_item.item.save()

        return super().delete(request, *args, **kwargs)


class BulkDeleteSoldItems(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Sold Items Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = SoldItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        sale_id = self.kwargs['sale_id']
        sale = validate_sale(sale_id, self.request.user)
        return queryset.filter(sale=sale)

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        queryset = self.get_queryset()
        sale = queryset.first().sale

        # Validate sold item sale delivery status
        status_validation = validate_deletion_for_delivered_parent_instance(sale)
        if isinstance(status_validation, Response):
            return status_validation

        # Validate ids and items for deletion
        result = validate_linked_items_for_deletion(ids, queryset, Sale)

        # Return Response if validation failed
        if isinstance(result, Response):
            return result

        # Perform deletion
        sale, items_for_deletion = result
        reset_sold_items(items_for_deletion)
        delete_count, _ = items_for_deletion.delete()

        return Response({'message': f'{delete_count} sold items successfully deleted.'},
                         status=status.HTTP_200_OK)


class GetSalesData(CreatedByUserMixin, generics.GenericAPIView):
    """Returns necessary data for the sales app"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Sale.objects.all()

    def get(self, request, *args, **kwargs):
        # User sales
        sales = self.get_queryset()

        # Delivery & Payment status
        sale_status = {
            'delivery_status': DELIVERY_STATUS_OPTIONS,
            'payment_status': PAYMENT_STATUS_OPTIONS
        }

        # Active sales
        active_sales = (
            sales.filter(delivery_status__name__in=ACTIVE_DELIVERY_STATUS)
            .count()
        )
        sale_status['active'] = active_sales

        # Completed sales
        completed_sales = (
            sales.filter(delivery_status__name__in=COMPLETED_STATUS)
            .count()
        )
        sale_status['completed'] = completed_sales

        # Completed sales
        failed_sales = (
            sales.filter(delivery_status__name__in=FAILED_STATUS)
            .count()
        )
        sale_status['failed'] = failed_sales

        return Response({'sales_count': sales.count(),
                         'sale_status': sale_status},
                         status=status.HTTP_200_OK)
