from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from utils.tokens import Token
from utils.views import CreatedByUserMixin
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Item, Category, Variant
from ..supplier_orders.models import Supplier


class CreateListItems(CreatedByUserMixin,
                      generics.ListCreateAPIView):
    """Handles Item Creation"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ItemSerializer
    parser_classes = (FormParser, MultiPartParser)
    queryset = Item.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        in_inventory = self.request.GET.get('in_inventory', None)
        if in_inventory and in_inventory.lower() == 'true':
            queryset = queryset.filter(in_inventory=True)
        return queryset


class GetUpdateDeleteItems(CreatedByUserMixin,
                          generics.RetrieveUpdateDestroyAPIView):
    """Handles Item's Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Item.objects.all()
    serializer_class = serializers.ItemSerializer
    parser_classes = (FormParser, MultiPartParser)
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        item = self.get_object()
        if 'empty_picture' in request.data:
            item.picture = None
            item.save()
        return super().put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        if item.total_client_orders > 0 or item.total_supplier_orders > 0 :
            return Response(
                {
                    'error': f'Item {item.name} is linked to existing orders. '
                                'Manage orders before deletion.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().delete(request, *args, **kwargs)


class BulkDeleteItems(CreatedByUserMixin,
                      generics.GenericAPIView):
    """Handles Items Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Item.objects.all()

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided."},
                            status=status.HTTP_400_BAD_REQUEST)
        # Validate ids
        items_invalid_ids = Token.validate_uuids(ids)
        if items_invalid_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all provided IDs are not valid UUIDs.',
                        'invalid_ids': items_invalid_ids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        items_found_ids = set(
            self.get_queryset()
            .filter(id__in=ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(ids) - items_found_ids
        if missing_ids:
            return Response(
                {
                    'error': 'Some or all items could not be found.',
                    'missing_ids': list(missing_ids)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Handle items with orders and without orders cases
        items_with_orders = (
            self.get_queryset()
            .filter(
                Q(clientordereditem__isnull=False) | Q(supplierordereditem__isnull=False),
                id__in=ids
            )
            .values('id', 'name')
            .distinct()
        )

        items_without_orders = (
            self.get_queryset()
            .filter(
                id__in=ids,
                clientordereditem__isnull=True,
                supplierordereditem__isnull=True)
        )
        items_without_orders_count = items_without_orders.count()
        # Case 1: All item items are linked to orders
        if items_with_orders.exists() and not items_without_orders.exists():
            return Response(
                {
                    'error': {
                        'message': 'All selected items are linked to '
                                   'existing orders. Manage orders before deletion.',
                        'linked_items': items_with_orders,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Case 2: Some items are linked to orders
        if items_with_orders.exists() and items_without_orders.exists():
            items_without_orders.delete()
            items_with_orders_count = items_with_orders.count()
            item_text = "items" if items_without_orders_count > 1 else "item"
            linked_item_text = "items" if items_with_orders_count > 1 else "item"
            return Response(
                {
                    'message': f'{items_without_orders_count} {item_text} deleted successfully, '
                               f'but {items_with_orders_count} {linked_item_text} '
                               f'could not be deleted because they are linked '
                                'to existing orders.',
                    'linked_items': items_with_orders
                },
                status=status.HTTP_207_MULTI_STATUS
            )
        # Case 3: None of the items are linked to orders
        items_without_orders.delete()
        return Response({'message': f'{items_without_orders_count} items successfully deleted.'},
                         status=status.HTTP_200_OK)


class GetInventoryData(generics.GenericAPIView):
    """Returns necessary data related to user's inventory"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        # Categories
        categories = {
            'count': Category.objects.filter(created_by=user).count(),
            'names': list(Category.objects.filter(created_by=user).values_list('name', flat=True))
        }

        suppliers = {
            'count': Supplier.objects.filter(created_by=user).count(),
            'names': list(Supplier.objects.filter(created_by=user).values_list('name', flat=True))
        }
        
        # Variants
        variants = list(Variant.objects.filter(created_by=user).values_list('name', flat=True))
        
        # Items
        user_items = Item.objects.filter(created_by=user, in_inventory=True)
        items = user_items.values('name', 'quantity')
        
        # Total Value & Total Quantity
        total_value = sum([item.total_price for item in user_items])
        total_quantity = sum(list(user_items.values_list('quantity', flat=True)))
        
        return Response({'items': items,
                         'total_items': user_items.count(),
                         'total_value': total_value,
                         'total_quantity': total_quantity,
                         'categories': categories,
                         'suppliers': suppliers,
                         'variants': variants},
                         status=status.HTTP_200_OK)
