from rest_framework import serializers
from django.db import transaction
from django.db.models import Q
from typing import List
from .utils import get_or_create_source, update_item_quantity
from utils.serializers import (datetime_repr_format,
                               get_location,
                               get_or_create_location,
                               update_field)
from utils.order_status import (DELIVERY_STATUS_OPTIONS_LOWER,
                                PAYMENT_STATUS_OPTIONS_LOWER)
from .models import (Client,
                     Country,
                     City,
                     Location,
                     AcquisitionSource,
                     ClientOrderedItem,
                     OrderStatus,
                     ClientOrder)
from ..inventory.models import Item
from ..base.models import User


class CountrySerializer(serializers.ModelSerializer):
    """Country Serializer"""
    class Meta:
        model = Country
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    """City Serializer"""
    class Meta:
        model = City
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    """Location Serializer"""
    country = serializers.CharField(error_messages={'null': 'Country is required to add a location'})
    city = serializers.CharField(error_messages={'null': 'City is required to add a location'})

    class Meta:
        model = Location
        fields = '__all__'

    def validate_country(self, value):
        if value:
            country = Country.objects.filter(name__iexact=value).exists()
            if not country:
                raise serializers.ValidationError("Invalid country.")
            return value
        return None
    
    def validate_city(self, value):
        if value:
            city = City.objects.filter(name__iexact=value).exists()
            if not city:
                raise serializers.ValidationError("Invalid city.")
            return value
        return None

    def validate(self, attrs):
        country_name = attrs.get('country', None)
        city_name = attrs.get('city', None)
        if country_name and city_name:
            city = City.objects.filter(name__iexact=city_name,
                                       country__name__iexact=country_name).first()
            if not city:
                raise serializers.ValidationError(
                    {'city': 'City does not belong to the country provided.'})
        return attrs

    def create(self, validated_data):
        user = self.context.get('user')
        if user:
            validated_data['added_by'] = user

        city_name = validated_data.pop('city', None)
        country_name = validated_data.pop('country', None)
        if country_name:
            validated_data['country'] = Country.objects.get(
                                        name__iexact=country_name)
        if city_name:
            validated_data['city'] = City.objects.get(
                                     name__iexact=city_name)

        # Define filter fields to determine which action to perform
        filter_fields = ['added_by', 'country', 'city', 'street_address']
        for field in filter_fields:
            if field not in validated_data:
                validated_data[field] = None

        location, created = Location.objects.get_or_create(**validated_data)

        return location


class AcquisitionSourceSerializer(serializers.ModelSerializer):
    """Acquisition Source Serializer"""
    class Meta:
        model = AcquisitionSource
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    """Client Serializer"""
    location = LocationSerializer(many=False, required=False, allow_null=True)
    source = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Client
        fields = [
            'id',
            'created_by',
            'name',
            'age',
            'phone_number',
            'email',
            'sex',
            'location',
            'source',
            'total_orders',
            'created_at',
            'updated_at',
            'updated',
        ]

    def validate_name(self, value):
        user = self.context.get('request').user
        if Client.objects.filter(
            created_by=user,
            name__iexact=value).exclude(
            pk=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("client with this name already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Extract the user from the context request
        user = self.context.get('request').user

        # Exclude special fields from validated_data
        location = validated_data.pop('location', None)
        source = validated_data.pop('source', None)

        # Create client with remaining validated data
        client = Client.objects.create(created_by=user, **validated_data)

        # Add client's location and source of acquisition
        if location:
            client.location = get_or_create_location(user, location)
        if source:
            client.source = get_or_create_source(user, source)
        client.save()

        return client

    @transaction.atomic
    def update(self, instance: Client, validated_data):
        # Extract the user from the context request
        user = self.context.get('request').user

        # Exclude special fields from validated_data
        location = validated_data.pop('location', None)
        source = validated_data.pop('source', None)

        # Update client with remaining validated data
        client = super().update(instance, validated_data)

        # Update client's location
        update_field(self,
                     client,
                     'location',
                     location,
                     get_or_create_location,
                     user)

        # Update client's source of acquisition
        update_field(self,
                     client,
                     'source',
                     source,
                     get_or_create_source,
                     user)

        client.updated = True
        client.save()

        return client

    def to_representation(self, instance: Client):
        client_repr = super().to_representation(instance)
        client_repr['created_by'] = instance.created_by.username
        client_repr['location'] = get_location(instance.location)
        client_repr['source'] = instance.source.name if instance.source else None
        client_repr['created_at'] = datetime_repr_format(instance.created_at)
        client_repr['updated_at'] = datetime_repr_format(instance.updated_at)
        return client_repr


class ClientOrderedItemSerializer(serializers.ModelSerializer):
    """Ordered Item Serializer"""
    item = serializers.CharField()

    class Meta:
        model = ClientOrderedItem
        fields = [
            'id',
            'order',
            'created_by',
            'item',
            'ordered_quantity',
            'ordered_price',
            'total_profit',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        # Get the request user from the context
        user = self.context['request'].user

        # Get the item name and quantity from the attributes
        item_name = attrs['item']
        ordered_quantity = attrs['ordered_quantity']

        # Check if the item exists in the user's inventory
        item = Item.objects.filter(created_by=user,
                                   name__iexact=item_name,
                                   in_inventory=True).first()
        if not item:
            raise serializers.ValidationError(
                {'item': f"Item {item_name} does not exist in your inventory."}
            )

        # Check if ordered quantity exceeds available stock
        if ordered_quantity > item.quantity:
            raise serializers.ValidationError(
                {'ordered_quantity': f"The ordered quantity for {item_name} exceeds available stock."}
            )

        return attrs

    def create(self, validated_data):
        item_name = validated_data.pop('item', None)
        item = Item.objects.filter(
            created_by=validated_data['created_by'],
            name__iexact=item_name
        ).first()
        item.quantity -= validated_data['ordered_quantity']
        item.save()
        return ClientOrderedItem.objects.create(item=item, **validated_data)


    def to_representation(self, instance: ClientOrderedItem):
        ordered_item_repr = super().to_representation(instance)
        ordered_item_repr['item'] = instance.item.name
        ordered_item_repr['created_by'] = instance.created_by.username
        ordered_item_repr['created_at'] = datetime_repr_format(instance.created_at)
        ordered_item_repr['updated_at'] = datetime_repr_format(instance.updated_at)
        return ordered_item_repr


class ClientOrderSerializer(serializers.ModelSerializer):
    """Order Serializer"""
    client = serializers.CharField()
    ordered_items = serializers.ListField(child=serializers.DictField(),
                                          write_only=True,
                                          required=True)
    delivery_status = serializers.CharField(required=False, allow_blank=True,
                                            allow_null=True)
    payment_status = serializers.CharField(required=False, allow_blank=True,
                                           allow_null=True)
    shipping_address = LocationSerializer(many=False, required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ClientOrder
        fields = [
            'id',
            'reference_id',
            'created_by',
            'client',
            'ordered_items',
            'delivery_status',
            'payment_status',
            'tracking_number',
            'shipping_address',
            'shipping_cost',
            'net_profit',
            'source',
            'created_at',
            'updated_at',
            'updated'
        ]

    def create_ordered_items_for_client_order(
        self,
        request,
        order: ClientOrder,
        user: User,
        ordered_items: List[dict],
    ):
        for item in ordered_items:
            item['order'] = order.id
            item['created_by'] = user.id
            serializer = ClientOrderedItemSerializer(data=item,
                                                     context={'request': request})
            if serializer.is_valid():
                serializer.save()
            else:
                raise serializers.ValidationError(serializer.errors)

    def update_ordered_items_for_client_order(
        self,
        request,
        order: ClientOrder,
        user: User,
        ordered_items: List[dict]):
        # Filter inventory items by old and new ordered items
        names_query = Q()
        items_names = [old_ordered_item.item.name for old_ordered_item in order.items]
        items_names.extend([new_ordered_item['item'] for new_ordered_item in ordered_items])
        for name in items_names:
            names_query |= Q(name__iexact=name)
        inventory_items = Item.objects.filter(names_query, created_by=user)
        # Create an inventory items map for all necessary items
        inventory_items_map = {
            item.name.lower(): item for item in inventory_items
        }
        # Create map of old/existing ordered items
        existing_items = {
            ordered_item.item.name.lower(): ordered_item for ordered_item in order.items
        }

        for new_item in ordered_items:
            existing_item = existing_items.pop(new_item['item'].lower(), None)
            # Update existing ordered item and item's quantity in inventory
            if existing_item:
                inventory_item = inventory_items_map.get(new_item['item'].lower())
                item_new_quantity = update_item_quantity(inventory_item,
                                                         existing_item.ordered_quantity,
                                                         new_item['ordered_quantity'])
                # Validate new item's quantity
                if item_new_quantity < 0:
                    raise serializers.ValidationError({
                        'ordered_items': {
                            'ordered_quantity': f"The ordered quantity for {inventory_item.name} exceeds available stock."
                        }
                    })
                else:
                    inventory_item.quantity = item_new_quantity
                    inventory_item.save()
                    existing_item.ordered_quantity = new_item['ordered_quantity']
                    existing_item.ordered_price = new_item['ordered_price']
                    existing_item.save()        
            # Create new ordered item
            else:
                self.create_ordered_items_for_client_order(request,
                                                           order,
                                                           user,
                                                           [new_item])

        # Delete remaining ordered items and update item's quantity in inventory
        for item_to_delete in existing_items.values():
            inventory_item = inventory_items_map.get(item_to_delete.item.name.lower())
            inventory_item.quantity += item_to_delete.ordered_quantity
            inventory_item.save()
            item_to_delete.delete()

    def get_ordered_items(self, order: ClientOrder):
        ordered_items = []
        for ordered_item in order.items:
            ordered_items.append({
                'item': ordered_item.item.name,
                'ordered_quantity': ordered_item.ordered_quantity,
                'ordered_price': ordered_item.ordered_price,
                'total_price': ordered_item.total_price,
                'total_profit': ordered_item.total_profit,
            })
        return ordered_items

    def validate_ordered_items(self, value: List[ClientOrderedItem]):
        unique_items = []
        for ordered_item in value:
            item_name = ordered_item['item'].lower()
            if item_name in unique_items:
                raise serializers.ValidationError(
                    {'item': f'Item {ordered_item["item"]} has been selected multiple times.'})
            else:
                unique_items.append(item_name)
        return value

    def validate_delivery_status(self, value):
        if value:
            if value.lower() not in DELIVERY_STATUS_OPTIONS_LOWER:
                raise serializers.ValidationError("Invalid order delivery status.")
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    def validate_payment_status(self, value):
        if value:
            if value.lower() not in PAYMENT_STATUS_OPTIONS_LOWER:
                raise serializers.ValidationError("Invalid order payment status.")
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    def validate(self, attrs):
        user = self.context.get('request').user
        client_name = attrs.get('client', None)
        if client_name:
            client = Client.objects.filter(
                created_by=user,
                name=client_name
            ).first()
            if not client:
                raise serializers.ValidationError(
                    {
                        'client': f"Client '{client_name}' does not exist. "
                                   "Please create a new client if this is a new entry."
                    }
                )

            attrs['client'] = client
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Extract the user from the context request
        request = self.context.get('request')
        user = request.user

        # Exclude special fields from validated_data
        ordered_items = validated_data.pop('ordered_items', None)
        shipping_address = validated_data.pop('shipping_address', None)
        source = validated_data.pop('source', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        # Create order with remaining data
        order = ClientOrder.objects.create(created_by=user, **validated_data)

        # Create and Add ordered items to the order
        self.create_ordered_items_for_client_order(
            request,
            order,
            user,
            ordered_items
        )

        # Update shipping address and source of acquisition and status to the order
        if shipping_address:
            order.shipping_address = get_or_create_location(user, shipping_address)
        if source:
            order.source = get_or_create_source(user, source)
        if delivery_status:
            order.delivery_status = delivery_status
        if payment_status:
            order.payment_status = payment_status

        order.save()
        return order

    @transaction.atomic
    def update(self, instance: ClientOrder, validated_data):
        # Extract the user from the context request
        request = self.context.get('request')
        user = request.user

        # Exclude special fields from validated_data
        ordered_items = validated_data.pop('ordered_items', None)
        shipping_address = validated_data.pop('shipping_address', None)
        source = validated_data.pop('source', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        # Update order with remaining data
        order = super().update(instance, validated_data)

        # Update ordered items of the order
        if ordered_items:
            self.update_ordered_items_for_client_order(
                request,
                order,
                user,
                ordered_items
            )

        # Update order's shipping address
        update_field(self,
                     order,
                     'shipping_address',
                     shipping_address,
                     get_or_create_location,
                     user)

        # Update order's source of acquisition
        update_field(self,
                     order,
                     'source',
                     source,
                     get_or_create_source,
                     user)

        # Update order's delivery and payment status
        if delivery_status:
            order.delivery_status = delivery_status
        if payment_status:
            order.payment_status = payment_status

        order.updated = True

        order.save()
        return order

    def to_representation(self, instance: ClientOrder):
        order_repr = super().to_representation(instance)
        order_repr['created_by'] = instance.created_by.username
        order_repr['source'] = instance.source.name if instance.source else None
        order_repr['ordered_items'] = self.get_ordered_items(instance)
        order_repr['shipping_address'] = get_location(instance.shipping_address)
        order_repr['created_at'] = datetime_repr_format(instance.created_at)
        order_repr['updated_at'] = datetime_repr_format(instance.updated_at)
        return order_repr
