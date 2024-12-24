from rest_framework import serializers
from django.db import transaction
from typing import List, Union
from utils.serializers import (datetime_repr_format,
                               get_location,
                               get_or_create_location,
                               validate_restricted_fields,
                               validate_changes_for_delivered_parent_instance)
from utils.status import (DELIVERY_STATUS_OPTIONS_LOWER,
                          PAYMENT_STATUS_OPTIONS_LOWER)
from utils.serializers import update_field, check_item_existence
from ..base.models import User
from ..inventory.models import Item
from ..client_orders.serializers import LocationSerializer
from ..client_orders.models import OrderStatus
from .models import Supplier, SupplierOrderedItem, SupplierOrder
from .utils import average_price


class SupplierSerializer(serializers.ModelSerializer):
    """Supplier Serializer"""
    location = LocationSerializer(many=False, required=False, allow_null=True)

    class Meta:
        model = Supplier
        fields = [
            'id',
            'created_by',
            'name',
            'phone_number',
            'email',
            'location',
            'total_orders',
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
        update_field(self,
                     supplier,
                     'location',
                     location,
                     get_or_create_location,
                     user)

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
    supplier = serializers.CharField()

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

    def _get_or_create_item_and_set_supplier(
        self,
        user: User,
        item_name: str,
        supplier: Supplier,
        ordered_quantity: int,
        ordered_price: int,
    ) -> Item:
        # Get or create ordered item with the order's supplier 
        item, created = Item.objects.get_or_create(
            name__iexact=item_name,
            defaults={
                'created_by': user,
                'supplier': supplier,
                'name': item_name,
                'quantity': ordered_quantity,
                'price': ordered_price,
            }
        )

        # Set item's supplier to the order's supplier for already existing item
        if not created and item.supplier is None:
            item.supplier = supplier
            item.save()

        return item
    
    def check_supplier_integrity(
        self,
        user: User,
        supplier: Supplier,
        item_name: Union[str, None],
        order: SupplierOrder,
    ) -> None:
        """
        Validate that the item's supplier and order's
        supplier match the given supplier.
        """
        # Check for existing item with a different supplier
        if item_name:
            item = Item.objects.filter(created_by=user,
                                    name__iexact=item_name).first()

            if item and item.supplier and (item.supplier != supplier):
                raise serializers.ValidationError(
                    {
                        'item': f"Item '{item_name}' is associated "
                                 "with another supplier."
                    }
                )

        # Ensure order's supplier matches the provided supplier
        if order.supplier != supplier:
            raise serializers.ValidationError(
                {
                    'supplier': f"Order's supplier '{order.supplier.name}' does "
                                f"not match the selected supplier '{supplier.name}'."
                }
            )
        
    def validate_item_uniqueness(
        self,
        item_name: str,
        order: SupplierOrder,
        instance: Union[SupplierOrderedItem, None]=None,
    ):
        item_exists = check_item_existence(SupplierOrderedItem,
                                           order,
                                           item_name,
                                           instance)
        if item_exists:
            raise serializers.ValidationError(
                {
                    'item': (
                        f"Item '{item_name}' already exists in the order's list of ordered items. "
                        "Consider updating the existing item if you need to modify its details."
                    )
                }
            )


    def validate_supplier(self, value):
        user = self.context.get('request').user
        supplier = Supplier.objects.filter(created_by=user,
                                           name__iexact=value).first()
        if not supplier:
            raise serializers.ValidationError(
                f"Supplier '{value}' does not exist. "
                 "Please create a new supplier if this is a new entry."
            )
        return supplier

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        item_name = validated_data.pop('item')
        supplier = validated_data.get('supplier')
        order = validated_data.get('order')

        # Validate item's order delivery status
        validate_changes_for_delivered_parent_instance(order)

        # Check supplier integrity
        self.check_supplier_integrity(user, supplier, item_name, order)

        # Validate item's uniqueness in the order's list of ordered items
        self.validate_item_uniqueness(item_name, order)

        # Get or create item
        item = self._get_or_create_item_and_set_supplier(
            user,
            item_name,
            validated_data['supplier'],
            validated_data['ordered_quantity'],
            validated_data['ordered_price']
        )

        # Return new supplier ordered item instance
        return SupplierOrderedItem.objects.create(
            created_by=user,
            item=item,
            **validated_data
        )

    @transaction.atomic
    def update(self, instance: SupplierOrderedItem, validated_data):
        user = self.context.get('request').user
        item_name = validated_data.pop('item', None)
        supplier = validated_data.get('supplier', instance.supplier)
        order = validated_data.get('order', instance.order)
        ordered_quantity = validated_data.get('ordered_quantity',
                                              instance.ordered_quantity)
        ordered_price = validated_data.get('ordered_price',
                                           instance.ordered_price)

        # Validate item's order delivery status
        validate_changes_for_delivered_parent_instance(order)

        # Check supplier integrity
        self.check_supplier_integrity(user, supplier, item_name, order)

        # Validate item's uniqueness in the order's list of ordered items
        self.validate_item_uniqueness(item_name, order, instance)

        # Update ordered item 
        if item_name:
            # Get or create item
            item = self._get_or_create_item_and_set_supplier(
                user,
                item_name,
                supplier,
                ordered_quantity,
                ordered_price
            )
            validated_data['item'] = item

        # Return updated supplier ordered item instance
        return super().update(instance, validated_data)

    def to_representation(self, instance: SupplierOrderedItem):
        item_to_repr = super().to_representation(instance)
        item_to_repr['created_by'] = (instance.created_by.username
                                      if instance.created_by else None)
        item_to_repr['supplier'] = instance.supplier.name
        item_to_repr['item'] = instance.item.name
        item_to_repr['in_inventory'] = instance.in_inventory
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
            'total_quantity',
            'total_price',
            'delivery_status',
            'payment_status',
            'tracking_number',
            'shipping_cost',
            'created_at',
            'updated_at',
            'updated'
        ]
    
    def get_ordered_items(self, instance: SupplierOrder):
        if instance.items:
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
        return None

    def create_ordered_items_for_supplier_order(
        self,
        request,
        order: SupplierOrder,
        supplier: Supplier,
        ordered_items: List[SupplierOrderedItem]):
        for item in ordered_items:
            item['order'] = order.id
            item['supplier'] = supplier.name
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
            raise serializers.ValidationError(
                f"Supplier '{value}' does not exist. "
                 "Please create a new supplier if this is a new entry.")
        return supplier

    def validate_ordered_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError('This field is required.')
        ordered_items = value
        unique_items = []
        for i, ordered_item in enumerate(ordered_items):
            if not ordered_item:
                raise serializers.ValidationError(
                    f"Item at position {i + 1} cannot be empty. Please provide valid details."
                )
            item_name = ordered_item['item'].lower()
            if item_name in unique_items:
                raise serializers.ValidationError(
                    {'item': f'Item {ordered_item["item"]} been selected multiple times.'})
            else:
                unique_items.append(item_name)
        return ordered_items

    def validate_delivery_status(self, value):
        if value:
            if value.lower() not in DELIVERY_STATUS_OPTIONS_LOWER:
                raise serializers.ValidationError('Invalid delivery status.')
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    def validate_payment_status(self, value):
        if value:
            if value.lower() not in PAYMENT_STATUS_OPTIONS_LOWER:
                raise serializers.ValidationError('Invalid payment status.')
            return OrderStatus.objects.filter(name__iexact=value).first()
        return None

    @transaction.atomic
    def create(self, validated_data):
        # Retrieve special fields
        request = self.context.get('request')
        user = request.user
        supplier = validated_data.get('supplier')
        ordered_items = validated_data.pop('ordered_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        # Create order
        order = SupplierOrder.objects.create(created_by=user, **validated_data)

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
        # Retrieve special fields
        request = self.context.get('request')
        user = request.user
        supplier = validated_data.get('supplier', instance.supplier)
        ordered_items = validated_data.pop('ordered_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)

        prev_delivery_status = instance.delivery_status.name

        # Validate if prev delivery status was set to 'Delivered'
        # and restricted fields were changed
        if instance.delivery_status.name == 'Delivered':
            order_data = self.to_representation(instance)
            keys_to_remove_from_items = ['total_price', 'in_inventory']
            validate_restricted_fields(
                instance,
                order_data,
                supplier,
                ordered_items,
                keys_to_remove_from_items,
                delivery_status
            )
    
        # Update order record
        order = super().update(instance, validated_data)

        # Update ordered items of the order
        if ordered_items:
            self.update_ordered_items_for_supplier_order(
                request,
                order,
                supplier,
                ordered_items
            )

        # Update delivery & payment status
        if delivery_status:
            order.delivery_status = delivery_status
        if payment_status:
            order.payment_status = payment_status

        # Update ordered items inventory state
        if (delivery_status and prev_delivery_status != 'Delivered'
            and delivery_status.name == 'Delivered'):
            self.update_ordered_items_inventory_state(user, order)

        order.updated = True
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
