from rest_framework import serializers
from django.db import transaction
from django.db.models import Q
from typing import List
from utils.serializers import (
    get_user,
    decimal_to_float,
    date_repr_format,
    get_location,
    get_or_create_location,
    get_or_create_source,
    update_item_quantity,
    update_field,
    check_item_existence,
    validate_restricted_fields,
    validate_changes_for_delivered_parent_instance
)
from utils.status import (
    DELIVERY_STATUS_OPTIONS_LOWER,
    PAYMENT_STATUS_OPTIONS_LOWER
)
from utils.activity import register_activity
from .models import Sale, SoldItem
from ..base.models import User
from ..inventory.models import Item
from ..client_orders.models import Client, OrderStatus
from ..client_orders.serializers import LocationSerializer


class SoldItemSerializer(serializers.ModelSerializer):
    """Sold Item Serializer"""
    sale = serializers.PrimaryKeyRelatedField(
        many=False,
        queryset=Sale.objects.all()
    )
    item = serializers.CharField()

    class Meta:
        model = SoldItem
        fields = [
            'id',
            'created_by',
            'sale',
            'item',
            'sold_quantity',
            'sold_price',
            'total_price',
            'total_profit',
            'unit_profit',
            'created_at',
            'updated_at'
        ]

    def validate_item(self, value):
        user = get_user(self.context)
        item = (
            Item.objects
            .filter(
                created_by=user,
                name__iexact=value,
                in_inventory=True)
            .first()
        )

        if not item:
            raise serializers.ValidationError(
                f"Item '{value}' does not exist in your inventory."
            )

        return item

    def validate_item_uniqueness(self, item_name: str, sale: Sale):
        item_exists = check_item_existence(SoldItem, sale, item_name)
        if item_exists:
            raise serializers.ValidationError(
                {
                    'item': (
                        f"Item '{item_name}' already exists in the sale's list of sold items. "
                        "Consider updating the existing item if you need to modify its details."
                    )
                }
            )

    def sold_quantity_validation_error(self, item_name: str):
        raise serializers.ValidationError(
            {
                'sold_quantity': f"The sold quantity for '{item_name}' "
                                    "exceeds available stock."
            }
        )

    @transaction.atomic
    def create(self, validated_data):
        # Extract special fields
        user = get_user(self.context)
        item = validated_data.get('item')
        sale = validated_data.get('sale')
        sold_quantity = validated_data.get('sold_quantity')

        # Validate item's sale delivery status
        validate_changes_for_delivered_parent_instance(sale)

        # Validate item's uniqueness in the order's list of sold items
        self.validate_item_uniqueness(item.name, sale)

        # Validate item's quantity and subtract sold quantity from inventory
        if item.quantity < sold_quantity:
            self.sold_quantity_validation_error(item.name)
        item.quantity -= sold_quantity
        item.save()

        # return sold item instance
        return SoldItem.objects.create(created_by=user, **validated_data)

    @transaction.atomic
    def update(self, instance: SoldItem, validated_data):
        # Extract special fields
        item = validated_data.get('item', None)
        sale = validated_data.get('sale', instance.sale)
        sold_quantity = validated_data.get('sold_quantity',
                                           instance.sold_quantity)        

        # Validate item's sale delivery status
        validate_changes_for_delivered_parent_instance(sale)

        # Case: Related item instance has changed
        if item and str(instance.item.id) != str(item.id):
            # Validate item's uniqueness in case item changed
            self.validate_item_uniqueness(item.name, sale)

            # Validate and update item's sold quantity
            if item.quantity < sold_quantity:
                self.sold_quantity_validation_error(item.name)

                # Reset prev item inventory quantity
                instance.item.quantity += instance.sold_quantity
                instance.item.save()

                # Subtract the ordered quantity from item's inventory quantity
                item.quantity -= sold_quantity
                item.save()

        # Case: Related item instance remained the same
        else:
            item = item or instance.item
            item_new_quantity = update_item_quantity(item,
                                                    instance.sold_quantity,
                                                    sold_quantity)
            # Validate new item's quantity
            if item_new_quantity < 0:
                self.sold_quantity_validation_error(item.name)

            else:
                # Update item's inventory quantity
                item.quantity = item_new_quantity
                item.save()

        # return sold item instance
        return super().update(instance, validated_data)

    def to_representation(self, instance: SoldItem):
        sold_item_repr = super().to_representation(instance)
        sold_item_repr['created_by'] = (instance.created_by.username
                                        if instance.created_by else None)
        sold_item_repr['item'] = instance.item.name
        sold_item_repr['sold_price'] = decimal_to_float(instance.sold_price)
        sold_item_repr['total_price'] = decimal_to_float(instance.total_price)
        sold_item_repr['total_profit'] = decimal_to_float(instance.total_profit)
        sold_item_repr['unit_profit'] = decimal_to_float(instance.unit_profit)
        sold_item_repr['created_at'] = date_repr_format(instance.created_at)
        sold_item_repr['updated_at'] = date_repr_format(instance.updated_at)
        return sold_item_repr


class SaleSerializer(serializers.ModelSerializer):
    """Sale Serializer"""
    client = serializers.CharField()
    sold_items = serializers.ListField(child=serializers.DictField(),
                                       required=True,
                                       write_only=True)
    delivery_status = serializers.CharField(allow_null=True,
                                            allow_blank=True,
                                            required=False)
    payment_status = serializers.CharField(allow_null=True,
                                           allow_blank=True,
                                           required=False)
    source = serializers.CharField(allow_null=True,
                                   allow_blank=True,
                                   required=False)
    shipping_address = LocationSerializer(many=False, required=False, allow_null=True)

    class Meta:
        model = Sale
        fields = [
            'id',
            'reference_id',
            'created_by',
            'client',
            'sold_items',
            'delivery_status',
            'payment_status',
            'source',
            'shipping_address',
            'shipping_cost',
            'tracking_number',
            'net_profit',
            'linked_order',
            'created_at',
            'updated_at',
            'updated',
        ]

    def get_sold_items(self, instance):
        if instance.items:
            sold_items = []
            for sold_item in instance.items:
                sold_items.append({
                    'item': sold_item.item.name,
                    'sold_quantity': sold_item.sold_quantity,
                    'sold_price': sold_item.sold_price,
                    'total_price': sold_item.total_price,
                    'total_profit': sold_item.total_profit
                })
            return sold_items
        return None

    def create_sold_items_for_sale(
        self,
        user: User,
        sale: Sale,
        sold_items: List[dict]
    ) -> None:
        for sold_item in sold_items:
            sold_item['sale'] = sale.id
            serializer = SoldItemSerializer(data=sold_item,
                                            context={'user': user})
            if serializer.is_valid():
                serializer.save()
            else:
                raise serializers.ValidationError(
                    {
                        'sold_items': serializer.errors
                    }
                )

    def update_sold_items_for_sale(
        self,
        user: User,
        sale: Sale,
        sold_items: List[dict]
    ) -> None:
        # Filter inventory items by old and new sold items
        item_names = [old_item.item.name for old_item in sale.items]
        item_names.extend([sold_item['item'] for sold_item in sold_items])
        names_query = Q()
        for name in item_names:
            names_query |= Q(name__iexact=name)
        inventory_items = Item.objects.filter(names_query, created_by=user)

        # Create an inventory items map for all necessary items
        inventory_items_map = {item.name.lower(): item for item in inventory_items}

        # Create map of old/existing sold items
        existing_items = {old_item.item.name.lower(): old_item
                          for old_item in sale.items}

        for sold_item in sold_items:
            existing_item = existing_items.pop(sold_item['item'].lower(), None)
            if existing_item:
                # Update existing sold item and item's quantity in inventory
                inventory_item = inventory_items_map.get(sold_item['item'].lower())
                new_item_quantity = update_item_quantity(inventory_item,
                                                         existing_item.sold_quantity,
                                                         sold_item['sold_quantity'])
                # Validate new item's quantity
                if new_item_quantity < 0:
                    raise serializers.ValidationError({
                        'sold_items': {
                            'sold_quantity': f"The sold quantity for '{sold_item['item']}' "
                                                "exceeds available stock."
                        }    
                    })
                else:
                    inventory_item.quantity = new_item_quantity
                    inventory_item.save()
                    existing_item.sold_quantity = sold_item['sold_quantity']
                    existing_item.sold_price = sold_item['sold_price']
                    existing_item.save()
    
            # Create new sold item
            else:
                self.create_sold_items_for_sale(user, sale, [sold_item])

        # Delete remaining sold items and update item's quantity in inventory
        for key, item_for_deletion in existing_items.items():
            inventory_item = inventory_items_map.get(key)
            inventory_item.quantity += item_for_deletion.sold_quantity
            inventory_item.save()
            item_for_deletion.delete()


    def update_linked_order(self, sale: Sale) -> None:
        from ..client_orders.serializers import ClientOrderSerializer

        order_sale_mutable_data = {
            'payment_status': sale.payment_status,
            'shipping_address': sale.shipping_address,
            'shipping_cost': sale.shipping_cost,
            'tracking_number': sale.tracking_number,
            'source': sale.source,
            'updated': True
        }

        serializer = ClientOrderSerializer(data=order_sale_mutable_data)
        serializer.update_without_validation(sale.order, serializer.initial_data)

    def prepare_sold_items(self, sale, items):
        return [
            SoldItem(
                sale=sale,
                created_by=sold_item.created_by,
                item=sold_item.item,
                sold_quantity=sold_item.ordered_quantity,
                sold_price=sold_item.ordered_price
            )
            for sold_item in items
        ]

    def validate_client(self, value):
        user = get_user(self.context)
        client = Client.objects.filter(
            created_by=user,
            name__iexact=value
        ).first()
        if not client:
            raise serializers.ValidationError(
                f"Client '{value}' does not exist. "
                 "Please create a new client if this is a new entry.")
        return client

    def validate_sold_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError('This field is required.')
        unique_items = []
        for i, sold_item in enumerate(value):
            if not sold_item:
                raise serializers.ValidationError(
                    f"Item at position {i + 1} cannot be empty. Please provide valid details."
                )
            if sold_item['item'].lower() in unique_items:
                sold_item_name = sold_item['item']
                raise serializers.ValidationError(
                    {'item': f"Item '{sold_item_name}' has been selected multiple times."}
                )
            else:
                unique_items.append(sold_item['item'].lower())

        return value

    def validate_delivery_status(self, value):
        if value:
            if value.lower() in DELIVERY_STATUS_OPTIONS_LOWER:
                return OrderStatus.objects.filter(name__iexact=value).first()
            else:
                raise serializers.ValidationError('Invalid delivery status.')
        return None

    def validate_payment_status(self, value):
        if value:
            if value.lower() in PAYMENT_STATUS_OPTIONS_LOWER: 
                return OrderStatus.objects.filter(name__iexact=value).first()
            else:
                raise serializers.ValidationError('Invalid payment status.')
        return None

    @transaction.atomic
    def create(self, validated_data):
        # Extract special fields
        user = get_user(self.context)
        sold_items = validated_data.pop('sold_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)
        shipping_address = validated_data.pop('shipping_address', None)
        source = validated_data.pop('source', None)

        # Create a sale with the remaining data
        sale = Sale.objects.create(created_by=user, **validated_data)

        # Add sold items to the sale
        self.create_sold_items_for_sale(user, sale, sold_items)

        # Add delivery and payment status if any
        if delivery_status:
            sale.delivery_status = delivery_status
        if payment_status:
            sale.payment_status = payment_status

        # Add shipping address if any
        if shipping_address:
            sale.shipping_address = get_or_create_location(
                user,
                shipping_address
            )

        # Add source of acquisition if any
        if source:
            sale.source = get_or_create_source(user, source)

        # Save changes and return sale instance
        sale.save()

        register_activity(user, "created", "sale", [sale.reference_id])

        return sale

    @transaction.atomic
    def create_without_validation(self, data: dict) -> Sale:
        # Extract special fields
        items = data.pop('sold_items')

        # Create a sale with the remaining data
        sale = Sale.objects.create(**data)
        sold_items = self.prepare_sold_items(sale, items)
        # Add sold items to the sale
        SoldItem.objects.bulk_create(sold_items)

        # Return sale instance
        return sale

    @transaction.atomic
    def update(self, instance: Sale, validated_data):
        # Extract special fields
        user = get_user(self.context)
        client = validated_data.get('client', instance.client)
        sold_items = validated_data.pop('sold_items', None)
        delivery_status = validated_data.pop('delivery_status', None)
        payment_status = validated_data.pop('payment_status', None)
        shipping_address = validated_data.pop('shipping_address', None)
        source = validated_data.pop('source', None)

        # Validate if prev delivery status was set to 'Delivered'
        # and restricted fields were changed
        if instance.delivery_status.name == 'Delivered':
            sale_data = self.to_representation(instance)
            keys_to_remove_from_items = ['total_price', 'total_profit']
            validate_restricted_fields(
                instance,
                sale_data,
                client,
                sold_items,
                keys_to_remove_from_items,
                delivery_status
            )

        # Update sale instance with the remaining data
        sale = super().update(instance, validated_data)

        # Update sale's sold items if any
        if sold_items:
            self.update_sold_items_for_sale(user, sale, sold_items)

        # Update delivery and payment status if any
        if delivery_status:
            sale.delivery_status = delivery_status
        if payment_status:
            sale.payment_status = payment_status

        # Update sale's shipping address
        update_field(self,
                     sale,
                     'shipping_address',
                     shipping_address,
                     get_or_create_location,
                     user)

        # Update sale's source of acquisition
        update_field(self,
                     sale,
                     'source',
                     source,
                     get_or_create_source,
                     user)

        # Save changes
        sale.updated = True
        sale.save()

        # Update sale's linked order if any
        if sale.has_order:
            self.update_linked_order(sale)
        
        register_activity(user, "updated", "sale", [sale.reference_id])

        # Return sale instance
        return sale

    @transaction.atomic
    def update_without_validation(self, instance: Sale, data: dict) -> Sale:
        sale = instance
        for field, value in data.items():
            setattr(sale, field, value)
        sale.save()

        return sale

    def to_representation(self, instance: Sale):
        sale_repr = super().to_representation(instance)
        sale_repr['created_by'] = (instance.created_by.username
                                   if instance.created_by else None)
        sale_repr['client'] = instance.client.name
        sale_repr['sold_items'] = self.get_sold_items(instance)
        sale_repr['delivery_status'] = instance.delivery_status.name
        sale_repr['payment_status'] = instance.payment_status.name
        sale_repr['net_profit'] = decimal_to_float(instance.net_profit)
        sale_repr['source'] = instance.source.name if instance.source else None
        sale_repr['shipping_address'] = get_location(instance.shipping_address)
        sale_repr['shipping_cost'] = (
            decimal_to_float(instance.shipping_cost)
            if instance.shipping_cost else None
        )
        sale_repr['created_at'] = date_repr_format(instance.created_at)
        sale_repr['updated_at'] = date_repr_format(instance.updated_at)
        return sale_repr
