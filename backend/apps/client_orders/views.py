from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..base.auth import TokenVersionAuthentication
from django.db.models import Q
from .utils import reset_client_ordered_items
from . import serializers
from .models import (Client,
                     ClientOrder,
                     Country,
                     City,
                     AcquisitionSource,
                     ClientOrderStatus)


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


class CreateListClientOrder(generics.ListCreateAPIView):
    """Handles Client Order Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderSerializer
    queryset = ClientOrder.objects.all()


class GetUpdateDeleteClientOrder(generics.RetrieveUpdateDestroyAPIView):
    """Handles Client Order Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderSerializer
    queryset = ClientOrder.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        reset_client_ordered_items(order)
        return super().destroy(request, *args, **kwargs)


class BulkDeleteClientOrders(generics.DestroyAPIView):
    """Handles Client Orders Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderSerializer
    queryset = ClientOrder.objects.all()

    def delete(self, request, *args, **kwargs):
        order_ids = request.data.get('ids', [])
        if not order_ids:
            return Response({'error': 'No IDs provided.'},
                            status=status.HTTP_400_BAD_REQUEST)

        orders = ClientOrder.objects.filter(id__in=order_ids)
        for order in orders:
            reset_client_ordered_items(order)
            order.delete()

        return Response({'message': 'orders have been successfully deleted'},
                         status=status.HTTP_200_OK)


class BulkCreateListCities(generics.ListCreateAPIView):
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
        # Clients
        clients = list(Client.objects.filter(created_by=user).values_list('name', flat=True))
        # Orders Count
        orders_count = ClientOrder.objects.filter(created_by=user).count()
        # Countries and Cities
        countries = []
        for country in Country.objects.all():
            countries.append(
                {'name': country.name,
                'cities': [city.name for city in country.cities.all()]})
        # Sources of Acquisition
        acq_sources = list(AcquisitionSource.objects.filter(
                           Q(added_by=user) | Q(added_by__isnull=True)
                           ).values_list('name', flat=True))
        # Status Names
        status_names = list(ClientOrderStatus.objects.all().values_list('name', flat=True))
        # Completed orders
        completed_status = ['Paid', 'Delivered']
        completed_orders = ClientOrder.objects.filter(created_by=user,
                                                      status__name__in=completed_status).count()
        # Active Orders
        active_status = ['Pending', 'Shipped']
        active_orders = ClientOrder.objects.filter(created_by=user,
                                                   status__name__in=active_status).count()
        # Failed Orders
        failed_status = ['Canceled', 'Failed', 'Refunded', 'Returned']
        failed_orders = ClientOrder.objects.filter(created_by=user,
                                                   status__name__in=failed_status).count()
        # Orders Status
        orders_status = {'names': status_names,
                         'active': active_orders,
                         'completed': completed_orders,
                         'failed': failed_orders}

        return Response({'clients': {'count': len(clients), 'names': clients},
                         'orders_count': orders_count,
                         'countries': countries,
                         'acq_sources': acq_sources,
                         'order_status': orders_status},
                         status=status.HTTP_200_OK)
