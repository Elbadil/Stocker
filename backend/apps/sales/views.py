from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django.db.models.functions import Cast
from django.db.models import CharField
from utils.views import CreatedByUserMixin
from utils.tokens import Token
from .utils import validate_sale, reset_sale_sold_items
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
        if not sale.from_order:
            reset_sale_sold_items(sale)

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
        delete_count = 0
        for sale in sales_for_deletion:
            if not sale.from_order:
                reset_sale_sold_items(sale)
            SoldItem.objects.filter(sale=sale).delete()
            sale.delete()
            delete_count += 1

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
        if not sold_item.sale.from_order:
            sold_item.item.quantity += sold_item.sold_quantity
            sold_item.item.save()

        return super().delete(request, *args, **kwargs)

# class BulkDeleteSoldItems(CreatedByUserMixin, generics.DestroyAPIView):
#     """Handles Sold Items Bulk Deletion"""
#     authentication_classes = (TokenVersionAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     queryset = SoldItem.objects.all()

#     def delete(self, request, *args, **kwargs):

#         return super().delete(request, *args, **kwargs)