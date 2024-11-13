from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Item, Category, Supplier, Variant
from ..client_orders.models import ClientOrderedItem


class CreateItem(generics.CreateAPIView):
    """Handles Item Creation"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ItemSerializer
    parser_classes = (FormParser, MultiPartParser)


class GetUpdateDeleteItem(generics.RetrieveUpdateDestroyAPIView):
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
        is_ordered = OrderedItem.objects.filter(item=item).exists()
        if is_ordered:
            return Response(
                    {'error': f'Item {item.name} is linked to existing orders. Manage orders before deletion.'},
                    status=status.HTTP_400_BAD_REQUEST)
        return super().delete(request, *args, **kwargs)


class ListUserItems(generics.ListAPIView):
    """Handles User Items Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ItemSerializer

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)


class ItemsBulkDelete(generics.GenericAPIView):
    """Handles Items Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No IDs provided."},
                            status=status.HTTP_400_BAD_REQUEST)

        ordered_items = list(ClientOrderedItem.objects.filter(
                            item__id__in=ids).values_list('item__name', flat=True))
        if ordered_items:
            return Response(
            {
                'error': {
                    'message': 'Some items are linked to existing orders. Manage orders before deletion.',
                    'linked_items': ordered_items
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        delete_count, _ = Item.objects.filter(id__in=ids).delete()
        return Response({'message': f'{delete_count} items deleted'},
                         status=status.HTTP_200_OK)


class GetUserInventoryData(generics.GenericAPIView):
    """Returns necessary data related to user's inventory"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        # Categories
        categories = {
            'count': Category.objects.filter(user=user).count(),
            'names': list(Category.objects.filter(user=user).values_list('name', flat=True))
        }
        # Suppliers
        suppliers = {
            'count': Supplier.objects.filter(user=user).count(),
            'names': list(Supplier.objects.filter(user=user).values_list('name', flat=True))
        }
        # Variants
        variants = list(Variant.objects.filter(user=user).values_list('name', flat=True))
        # Items
        user_items = Item.objects.filter(user=user)
        items = []
        for item in user_items:
            client_ordered = ClientOrderedItem.objects.filter(item=item).exists()
            items.append({'name': item.name,
                          'quantity': item.quantity,
                          'ordered': client_ordered})
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


class CreateCategory(generics.CreateAPIView):
    """Handles Item's Category Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CategorySerializer


class GetUpdateDeleteCategory(generics.RetrieveUpdateDestroyAPIView):
    """Handles Item's Category Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    lookup_field = 'id'
