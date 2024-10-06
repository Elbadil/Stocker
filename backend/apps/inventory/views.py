from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.utils.datastructures import MultiValueDict
import json
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Item, Category, Supplier, Variant


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


class ListUserItems(generics.GenericAPIView):
    """Handles User Items Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ItemSerializer

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        query_set = self.get_queryset()
        total_categories = Category.objects.filter(item__in=query_set).distinct().count()
        total_suppliers = Supplier.objects.filter(item__in=query_set).distinct().count()
        items = self.get_serializer(query_set, many=True).data
        return Response({'total': query_set.count(),
                         'categories': total_categories,
                         'suppliers': total_suppliers,
                         'items': items},
                         status=status.HTTP_200_OK)


class GetUserInventoryData(generics.GenericAPIView):
    """Returns necessary data related to user's inventory"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        categories = {
            'count': Category.objects.filter(user=user).count(),
            'names': list(Category.objects.filter(user=user).values_list('name', flat=True))
        }
        suppliers = {
            'count': Supplier.objects.filter(user=user).count(),
            'names': list(Supplier.objects.filter(user=user).values_list('name', flat=True))
        }
        variants = list(Variant.objects.filter(user=user).values_list('name', flat=True))
        return Response({'categories': categories,
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
