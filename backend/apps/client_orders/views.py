from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, CharField
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
from ..base.auth import TokenVersionAuthentication
from ..inventory.models import Item
from .utils import validate_client_order, reset_client_ordered_items
from . import serializers
from .models import (Client,
                     ClientOrder,
                     ClientOrderedItem,
                     Country,
                     City,
                     AcquisitionSource)


class CreateListClients(CreatedByUserMixin,
                       generics.ListCreateAPIView):
    """Handles Client Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientSerializer
    queryset = Client.objects.all()


class GetUpdateDeleteClients(CreatedByUserMixin,
                            generics.RetrieveUpdateDestroyAPIView):
    """Handles Client Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientSerializer
    queryset = Client.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        if client.total_orders > 0:
            return Response(
                {
                    'error': f'Client {client.name} is linked to existing orders. '
                            'Manage orders before deletion.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().delete(request, *args, **kwargs)


class BulkDeleteClients(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Client Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Client.objects.all()

    def delete(self, request, *args, **kwargs):
        clients_ids = request.data.get('ids', [])
        if not clients_ids:
            return Response({"error": "No IDs provided."},
                            status=status.HTTP_400_BAD_REQUEST)
        # Validate ids
        clients_invalid_ids = Token.validate_uuids(clients_ids)
        if clients_invalid_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all provided IDs are not valid UUIDs.',
                        'invalid_ids': clients_invalid_ids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        clients_found_ids = set(
            self.get_queryset()
            .filter(id__in=clients_ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(clients_ids) - clients_found_ids
        if missing_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all clients could not be found.',
                        'missing_ids': list(missing_ids)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Handle client with orders and without orders cases
        clients_with_orders = (
            self.get_queryset()
            .filter(
                id__in=clients_ids,
                orders__isnull=False)
            .values('id', 'name')
            .distinct()
        )
        clients_without_orders = (
            self.get_queryset()
            .filter(
                id__in=clients_ids,
                orders__isnull=True)
        )
        # Case 1: All clients have orders
        if clients_with_orders.exists() and not clients_without_orders.exists():
            return Response(
                {
                    'error': {
                        'message': 'All selected clients are linked to '
                                   'existing orders. Manage orders before deletion.',
                        'linked_clients': clients_with_orders,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Case 2: Some clients have orders
        if clients_with_orders.exists() and clients_without_orders.exists():
            delete_count, _ = clients_without_orders.delete()
            clients_with_orders_count = clients_with_orders.count()
            client_text = "clients" if delete_count > 1 else "client"
            linked_client_text = "clients" if clients_with_orders_count > 1 else "client"
            return Response(
                {
                    'message': f'{delete_count} {client_text} deleted successfully, '
                               f'but {clients_with_orders_count} {linked_client_text} '
                               f'could not be deleted because they are linked '
                                'to existing orders.',
                    'linked_clients': clients_with_orders
                },
                status=status.HTTP_207_MULTI_STATUS
            )
        # Case 3: None of the clients have orders
        delete_count, _ = clients_without_orders.delete()
        return Response({'message': f'{delete_count} clients successfully deleted.'},
                         status=status.HTTP_200_OK)


class CreateListClientOrders(CreatedByUserMixin,
                            generics.ListCreateAPIView):
    """Handles Client Order Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderSerializer
    queryset = ClientOrder.objects.all()


class GetUpdateDeleteClientOrders(CreatedByUserMixin,
                                 generics.RetrieveUpdateDestroyAPIView):
    """Handles Client Order Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderSerializer
    queryset = ClientOrder.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        if not order.sale:
            reset_client_ordered_items(order.items)
        ClientOrderedItem.objects.filter(order=order).delete()
        return super().destroy(request, *args, **kwargs)


class BulkDeleteClientOrders(CreatedByUserMixin, generics.DestroyAPIView):
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
        # Validate ids
        orders_invalid_ids = Token.validate_uuids(order_ids)
        if orders_invalid_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all provided IDs are not valid UUIDs.',
                        'invalid_ids': orders_invalid_ids
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        orders_found_ids = set(
            self.get_queryset()
            .filter(
                id__in=order_ids)
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )
        missing_ids = set(order_ids) - orders_found_ids
        if missing_ids:
            return Response(
                {
                    'error': {
                        'message': 'Some or all selected orders could not be found.',
                        'missing_ids': list(missing_ids)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        # Reset items quantities linked to the orders and delete
        orders = self.get_queryset().filter(id__in=order_ids)
        delete_count = 0
        for order in orders:
            if not order.sale:
                reset_client_ordered_items(order.items)
            ClientOrderedItem.objects.filter(order=order).delete()
            order.delete()
            delete_count += 1

        return Response({'message': f'{delete_count} client orders successfully deleted.'},
                         status=status.HTTP_200_OK)


class CreateListClientOrderedItems(CreatedByUserMixin,
                                  generics.ListCreateAPIView):
    """Handles Client Ordered Item Creation and Listing"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderedItemSerializer
    queryset = ClientOrderedItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_client_order(order_id, self.request.user)
        return queryset.filter(order=order)

    def perform_create(self, serializer):
        order_id = self.kwargs['order_id']
        order = validate_client_order(order_id, self.request.user)
        serializer.save(order=order)


class GetUpdateDeleteClientOrderedItems(CreatedByUserMixin,
                                       generics.RetrieveUpdateDestroyAPIView):
    """Handles Client Ordered Item Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClientOrderedItemSerializer
    queryset = ClientOrderedItem.objects.all()
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_client_order(order_id, self.request.user)
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

        # Reset item inventory's quantity
        inventory_item = Item.objects.get(id=ordered_item.item.id)
        inventory_item.quantity += ordered_item.ordered_quantity
        inventory_item.save()

        # Delete ordered item
        ordered_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkDeleteClientOrderedItems(CreatedByUserMixin, generics.DestroyAPIView):
    """Handles Client Ordered Items Bulk Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ClientOrderedItem.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        order_id = self.kwargs['order_id']
        order = validate_client_order(order_id, self.request.user)
        return queryset.filter(order=order)
    
    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        queryset = self.get_queryset()
        order = queryset.first().order

        # Validate ordered item order delivery status
        status_validation = validate_deletion_for_delivered_parent_instance(order)
        if isinstance(status_validation, Response):
            return status_validation

        # Validate ids and items for deletion
        result = validate_linked_items_for_deletion(ids, queryset, ClientOrder)

        # Return Response if validation failed
        if isinstance(result, Response):
            return result

        # Perform items deletion
        order, items_for_deletion = result
        reset_client_ordered_items(order.items)
        delete_count, _ = items_for_deletion.delete()

        return Response({'message': f'{delete_count} ordered items successfully deleted.'},
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
        acq_sources = list(
            AcquisitionSource.objects
            .filter(
                Q(added_by=user) | Q(added_by__isnull=True))
            .values_list('name', flat=True)
        )

        # Completed orders
        completed_orders = (
            ClientOrder.objects
            .filter(
                created_by=user,
                delivery_status__name__in=COMPLETED_STATUS)
            .count()
        )

        # Active Orders
        active_orders = (
            ClientOrder.objects
            .filter(
                created_by=user,
                delivery_status__name__in=ACTIVE_DELIVERY_STATUS)
            .count()
        )

        # Failed Orders
        failed_orders = (
            ClientOrder.objects
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

        return Response({'clients': {'count': len(clients), 'names': clients},
                         'orders_count': orders_count,
                         'countries': countries,
                         'acq_sources': acq_sources,
                         'order_status': orders_status},
                         status=status.HTTP_200_OK)
