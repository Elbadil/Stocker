from rest_framework import serializers
from django.db import transaction
from typing import List
from utils.serializers import (datetime_repr_format,
                               get_location,
                               get_or_create_location,
                               DELIVERY_STATUS_OPTIONS,
                               PAYMENT_STATUS_OPTIONS)
from ..base.models import User
from ..inventory.models import Item
from ..client_orders.serializers import LocationSerializer
from ..client_orders.models import OrderStatus
from .models import Supplier, SupplierOrderedItem, SupplierOrder
from .utils import average_price


class SupplierSerializer(serializers.ModelSerializer):
    """Supplier Serializer"""
    location = LocationSerializer(many=False, required=False)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'created_by',
            'name',
            'phone_number',
            'email',
            'location',
            'created_at',
            'updated_at',
            'updated',
        ]

    def validate_name(self, value):
        if value:
            if Supplier.objects.filter(name__iexact=value)\
                                .exclude(id=self.instance.id
                                         if self.instance else None)\
                                .exists():
                raise serializers.ValidationError(
                    'Supplier with this name already exists.')
            return value
        return None

    @transaction.atomic
    def create(self, validated_data):
        # Retrieve special fields
        user = self.context.get('request').user
        location = validated_data.pop('location', None)

        # Create supplier
        supplier = Supplier.objects.create(created_by=user, **validated_data)

        # Add location if any
        if location:
            supplier.location = get_or_create_location(user, location)
            supplier.save()
        
        return supplier
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # Retrieve special fields
        user = self.context.get('request').user
        location = validated_data.pop('location', None)

        # Update supplier
        supplier = super().update(instance, validated_data)

        # Update location if any
        if location:
            supplier.location = get_or_create_location(user, location)

        supplier.updated = True
        supplier.save()

        return supplier

    def to_representation(self, instance: Supplier):
        supplier_to_repr = super().to_representation(instance)
        supplier_to_repr['created_by'] = instance.created_by.username if instance.created_by else None
        supplier_to_repr['location'] = get_location(instance.location)
        supplier_to_repr['created_at'] = datetime_repr_format(instance.created_at)
        supplier_to_repr['updated_at'] = datetime_repr_format(instance.updated_at)
        return supplier_to_repr


class SupplierOrderedItemSerializer(serializers.ModelSerializer):
    """Supplier Ordered Item Serializer"""
    item = serializers.CharField()

    class Meta:
        model = SupplierOrderedItem
        fields = [
            'id',
            'order',
            'created_by',
            'supplier',
            'item',
            'ordered_quantity',
            'ordered_price',
            'created_at',
            'updated_at'
        ]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        item_name = validated_data.pop('item', None)

        item, created = Item.objects.get_or_create(
            name__iexact=item_name,
            defaults={
                'created_by': user,
                'supplier': validated_data['supplier'],
                'name': item_name,
                'quantity': validated_data['ordered_quantity'],
                'price': validated_data['ordered_price'],
            }
        )
        return SupplierOrderedItem.objects.create(created_by=user,
                                                  item=item,
                                                  **validated_data)

    def to_representation(self, instance: SupplierOrderedItem):
        item_to_repr = super().to_representation(instance)
        item_to_repr['created_by'] = instance.created_by.username if instance.created_by else None
        item_to_repr['supplier'] = instance.supplier.name
        item_to_repr['item'] = instance.item.name
        item_to_repr['created_at'] = datetime_repr_format(instance.created_at)
        item_to_repr['updated_at'] = datetime_repr_format(instance.updated_at)
        return item_to_repr


class SupplierOrderSerializer(serializers.ModelSerializer):
    """Supplier Order Serializer"""
    supplier = serializers.CharField()
    delivery_status = serializers.CharField(required=False,
                                            allow_null=True,
                                            allow_blank=True)
    payment_status = serializers.CharField(required=False,
                                           allow_null=True,
                                           allow_blank=True)
    ordered_items = serializers.ListField(child=serializers.DictField(),
                                          write_only=True,
                                          required=True)

    class Meta:
        model = SupplierOrder
        fields = [
            'id',
            'reference_id',
            'created_by',
            'supplier',
            'ordered_items',
            'delivery_status',
            'payment_status',
            'tracking_number',
            'shipping_cost',
            'created_at',
            'updated_at',
            'updated'
        ]
    
    def get_ordered_items(self, instance: SupplierOrder):
        ordered_items = []
        for ordered_item in instance.items:
            ordered_items.append({
                'item': ordered_item.item.name,
                'ordered_quantity': ordered_item.ordered_quantity,
                'ordered_price': ordered_item.ordered_price,
                'total_price': ordered_item.total_price,
                'in_inventory': ordered_item.in_inventory
            })
        return ordered_items

    def create_ordered_items_for_supplier_order(
        self,
        request,
        order: SupplierOrder,
        supplier: Supplier,
        ordered_items: List[SupplierOrderedItem]):
        for item in ordered_items:
            item['order'] = order.id
            item['supplier'] = supplier.id
            serializer = SupplierOrderedItemSerializer(data=item,
                                                       context={'request': request})
            if serializer.is_valid():
                serializer.save()
            else:
                raise serializers.ValidationError({'ordered_items': serializer.errors})

    def update_ordered_items_for_supplier_order(
        self,
        request,
        order: SupplierOrder,
        supplier: Supplier,
        ordered_items: List[SupplierOrderedItem]):
        existing_items = {
            ordered_item.item.name.lower(): ordered_item for ordered_item in order.items
        }

        for new_item in ordered_items:
            existing_item = existing_items.pop(new_item['item'].lower(), None)
            if existing_item:
                # Update existing ordered item
                existing_item.ordered_quantity = new_item['ordered_quantity']
                existing_item.ordered_price = new_item['ordered_price']
                existing_item.save()
            else:
                # Create new ordered item
                self.create_ordered_items_for_supplier_order(request,
                                                             order,
                                                             supplier,
                                                             [new_item])

        # Delete any remaining old items
        for item_to_delete in existing_items.values():
            item_to_delete.delete()

    def update_ordered_items_inventory_state(
        self,
        user: User,
        instance: SupplierOrder):
        item_ids = [ordered_item.item.id for ordered_item in instance.items]
        items = Item.objects.filter(created_by=user, id__in=item_ids)
        item_map = {item.id: item for item in items}
        for ordered_item in instance.items:
            item = item_map.get(ordered_item.item.id)
            # Update Item details in the inventory
            if item.in_inventory:
                if item.price == ordered_item.ordered_price:
                    # Update only item's quantity
                    item.quantity += ordered_item.ordered_quantity
                else:
                    # Calculate item's new price and update quantity
                    item.price = average_price(item, ordered_item)
                    item.quantity += ordered_item.ordered_quantity
            # Add Item to the inventory with the ordered item details
            else:
                # Add item to inventory
                item.quantity = ordered_item.ordered_quantity
                item.price = ordered_item.ordered_price
                item.in_inventory = True
            item.save()

    def validate_supplier(self, value):
        user = self.context.get('request').user
        supplier = Supplier.objects.filter(created_by=user,
                                           name__iexact=value).first()
        if not supplier:
            raise serializers.ValidationError(f'Supplier {value} does not exist.')
        return supplier

    def validate_ordered_items(self, value):
        ordered_items = value
        unique_items = []
        for ordered_item in ordered_items:
            item_name = ordered_item['item'].lower()
            if item_name in unique_items:
                raise serializers.ValidationError(
                    {'item': f'Item {ordered_item["item"]} been selected multiple times.'})
            else:
                unique_items.append(item_name)
        return ordered_items

    def validate_delivery_status(self, value):
        if value:
            if value.lower() not in DELIVERY_STATUS_OPTIONS:
                raise serializers.ValidationError('Invalid delivery status.')
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    def validate_payment_status(self, value):
        if value:
            if value.lower() not in PAYMENT_STATUS_OPTIONS:
                raise serializers.ValidationError('Invalid payment status.')
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    @transaction.atomic
    def create(self, validated_data):
        # Retrieve special fields
        request = self.context.get('request')
        user = request.user
        supplier = validated_data.pop('supplier', None)
        ordered_items = validated_data.pop('ordered_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        # Create order
        order = SupplierOrder.objects.create(created_by=user, **validated_data)

        # Add supplier to the order
        order.supplier = supplier

        # Create and add ordered items to order
        self.create_ordered_items_for_supplier_order(
            request,
            order,
            supplier,
            ordered_items
        )

        # Add delivery status
        if delivery_status:
            if delivery_status.name == 'Delivered':
                # Update ordered items inventory state
                self.update_ordered_items_inventory_state(user, order)
            order.delivery_status = delivery_status

        # Add payment status
        if payment_status:
            order.payment_status = payment_status

        order.save()
        return order

    @transaction.atomic
    def update(self, instance: SupplierOrder, validated_data):
        # Validate if order can be updated
        if instance.delivery_status.name == 'Delivered':
            raise serializers.ValidationError({
                'error': 'This order has already been marked as delivered and cannot be modified.'})

        # Retrieve special fields
        request = self.context.get('request')
        user = request.user
        supplier = validated_data.pop('supplier', None)
        ordered_items = validated_data.pop('ordered_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        # Update order record
        order = super().update(instance, validated_data)

        # Update supplier to the order
        if supplier != order.supplier:
            order.supplier = supplier

        # Update ordered items of the order
        if ordered_items:
            self.update_ordered_items_for_supplier_order(
                request,
                order,
                supplier,
                ordered_items
            )

        # Update delivery status
        if delivery_status:
            if delivery_status.name == 'Delivered':
                # Update ordered items inventory state
                self.update_ordered_items_inventory_state(user, order)
            order.delivery_status = delivery_status

        # Update payment status
        if payment_status:
            order.payment_status = payment_status

        order.save()
        return order

    def to_representation(self, instance: SupplierOrder):
        order_repr = super().to_representation(instance)
        order_repr['created_by'] = instance.created_by.username if instance.created_by else None
        order_repr['supplier'] = instance.supplier.name
        order_repr['ordered_items'] = self.get_ordered_items(instance)
        order_repr['delivery_status'] = instance.delivery_status.name
        order_repr['payment_status'] = instance.payment_status.name
        order_repr['created_at'] = datetime_repr_format(instance.created_at)
        order_repr['updated_at'] = datetime_repr_format(instance.updated_at)

        return order_repr
