from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..base.auth import TokenVersionAuthentication
from . import serializers
from .models import Client, Order, OrderedItem, City


class CreateListClient(generics.ListCreateAPIView):
    """Handles Client Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientSerializer
    queryset = Client.objects.all()


class GetUpdateDeleteClient(generics.RetrieveUpdateDestroyAPIView):
    """Handles Client Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientSerializer
    queryset = Client.objects.all()
    lookup_field = 'id'


class CreateListOrder(generics.ListCreateAPIView):
    """Handles Order Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.OrderSerializer
    queryset = Order.objects.all()


class GetUpdateDeleteOrder(generics.RetrieveUpdateDestroyAPIView):
    """Handles Order Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.OrderSerializer
    queryset = Order.objects.all()
    lookup_field = 'id'


class BulkCreateListCity(generics.ListCreateAPIView):
    """Handles Location Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CitySerializer
    queryset = City.objects.all()

    def perform_create(self, serializer):
        city_data = serializer.validated_data
        cities = [City(**item) for item in city_data]
        # Perform a single SQL query to insert multiple records
        # instead of inserting each instance individually
        City.objects.bulk_create(cities) 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
