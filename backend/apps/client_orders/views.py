from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..base.auth import TokenVersionAuthentication
from django.db.models import Q
from . import serializers
from .models import (Client,
                     Order,
                     Country,
                     City,
                     AcquisitionSource,
                     OrderStatus)


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


class BulkDeleteClients(generics.DestroyAPIView):
    """Handles Client Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        clients_ids = request.data.get('ids', [])
        if not clients_ids:
            return Response({"error": "No IDs provided."},
                            status=status.HTTP_400_BAD_REQUEST)
        delete_count, _ = Client.objects.filter(id__in=clients_ids).delete()
        return Response({'message': f'{delete_count} clients deleted'},
                         status=status.HTTP_200_OK)


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


class GetClientOrdersData(generics.GenericAPIView):
    """Returns necessary data related to user's client orders"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        clients = list(Client.objects.filter(created_by=user).values_list('name', flat=True))
        orders_count = Order.objects.filter(created_by=user).count()
        countries = []
        for country in Country.objects.all():
            countries.append(
                {'name': country.name,
                'cities': [city.name for city in country.cities.all()]})
        acq_sources = list(AcquisitionSource.objects.filter(
                           Q(added_by=user) | Q(added_by__isnull=True)
                           ).values_list('name', flat=True))
        order_status = list(OrderStatus.objects.all().values_list('name', flat=True))
        return Response({'clients': {'count': len(clients), 'names': clients},
                         'orders_count': orders_count,
                         'countries': countries,
                         'acq_sources': acq_sources,
                         'order_status': order_status},
                         status=status.HTTP_200_OK)
