from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError
import json
from utils.serializers import (
    get_user,
    handle_null_fields,
    update_field,
    date_repr_format
)
from utils.activity import register_activity
from ..base.models import User
from .models import Item, Category, Variant, VariantOption
from ..supplier_orders.models import Supplier


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""
    class Meta:
        model = Category
        fields = "__all__"


class VariantOptionSerializer(serializers.ModelSerializer):
    """Variant Serializer"""
    class Meta:
        model = VariantOption
        fields = "__all__"


class VariantSerializer(serializers.ModelSerializer):
    """Variant Serializer"""
    class Meta:
        model = Variant
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    """Item Serializer"""
    category = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    supplier = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    variants = serializers.CharField(write_only=True, required=False, allow_null=True)
    in_inventory = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Item
        fields = [
            'id',
            'created_by',
            'name',
            'quantity',
            'price',
            'total_price',
            'category',
            'supplier',
            'picture',
            'variants',
            'total_client_orders',
            'total_supplier_orders',
            'in_inventory',
            'created_at',
            'updated_at',
            'updated',
        ]

    def get_variants(self, item: Item):
        variants = []
        for variant in item.variants.all():
            variant_options = VariantOption.objects.filter(variant=variant, item=item)
            variants.append(
                {'name': variant.name,
                'options': [option.body for option in variant_options]}
            )
        return variants if len(variants) > 0 else None

    def _get_or_create_category(
        self, 
        user: User, 
        value: str
    ) -> Category:
        obj, created = Category.objects.get_or_create(
            created_by=user,
            name__iexact=value,
            defaults={'name': value})
        return obj

    def _get_or_create_variants_with_options(
        self, 
        item: Item, 
        user: User, 
        variants: list
    ) -> None:
        for variant_data in variants:
            variant_name = variant_data.get('name')
            variant_options = variant_data.get('options', [])

            # Getting or creating variant
            variant, created = Variant.objects.get_or_create(
                name__iexact=variant_name,
                defaults={'name': variant_name},
                created_by=user
            )

            # Adding variant to item's variants
            item.variants.add(variant)

            # Creating variant options
            unique_options = set()
            for option in variant_options:
                lower_option = option.lower()
                if lower_option not in unique_options:
                    VariantOption.objects.create(
                        item=item,
                        variant=variant,
                        body=option
                    )
                    unique_options.add(lower_option)

    def validate_name(self, value):
        user = get_user(self.context)
        if Item.objects.filter(
            created_by=user,
            name__iexact=value).exclude(pk=self.instance.id
                                        if self.instance
                                        else None).exists():
            raise ValidationError('Item with this name already exists.')
        return value

    def validate_supplier(self, value):
        if value:
            if value == 'null':
                return value
            user = get_user(self.context)
            supplier = Supplier.objects.filter(created_by=user,
                                               name__iexact=value).first()
            if not supplier:
                raise serializers.ValidationError(
                    f"Supplier '{value}' does not exist. "
                     "Please create a new supplier if this is a new entry.")

            return supplier

        return None

    def validate_variants(self, value):
        if value:
            if value == 'null':
                return value
            try:
                unique_variants = []
                variants = json.loads(value) if isinstance(value, str) else value
                # Ensuring it's a list of dictionaries
                if not isinstance(variants, list):
                    raise serializers.ValidationError("Variants must be a list.")

                # Validating each variant object
                for variant in variants:
                    if not isinstance(variant, dict):
                        raise serializers.ValidationError(
                            "Each variant must be an object with 'name' and 'options' as properties.")
                    # Checking required keys: 'name' and 'options'
                    if 'name' not in variant:
                        raise serializers.ValidationError("Each variant must have a 'name'.")
                    if 'options' not in variant or not isinstance(variant['options'], list):
                        raise serializers.ValidationError("Each variant must have an 'options' list.")
                    if variant['name'].lower() in unique_variants:
                        raise serializers.ValidationError("Each variant name should be unique.")
                    unique_variants.append(variant['name'].lower())

                return variants
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for variants.")
        return None

    def validate_picture(self, value):
        max_size = 2 * 1024 * 1024
        if value and value.size > max_size:
            raise serializers.ValidationError(
                "Picture size must be less than 2MB."
            )
        return value

    def validate(self, attrs):
        return handle_null_fields(attrs)

    @transaction.atomic
    def create(self, validated_data):
        user = get_user(self.context)
        variants = validated_data.pop('variants', None)
        category_name = validated_data.pop('category', None)
        supplier = validated_data.pop('supplier', None)
        in_inventory = validated_data.pop('in_inventory', None)

        # Creating Item's main fields
        item = Item.objects.create(created_by=user, **validated_data)

        # Creating Item's category
        if category_name:
            item.category = self._get_or_create_category(user, category_name)

        # Creating Item's supplier
        if supplier:
            item.supplier = supplier

        # Handle item's inventory state
        if (in_inventory and in_inventory == 'true') or not in_inventory:
            item.in_inventory = True

        item.save()

        # Creating and Adding Item's variants with options
        if variants:
            self._get_or_create_variants_with_options(item, user, variants)
        
        register_activity(user, "created", "item", [item.name])

        return item

    @transaction.atomic
    def update(self, instance: Item, validated_data):
        variants = validated_data.pop('variants', None)
        category_name = validated_data.pop('category', None)
        supplier = validated_data.pop('supplier', None)

        # Updating Item's main fields
        item = super().update(instance, validated_data)
        user = get_user(self.context)

        # Updating Item's category
        update_field(
            self,
            item,
            'category',
            category_name,
            self._get_or_create_category,
            user
        )

        # Updating Item's supplier
        update_field(self, item, 'supplier', supplier)

        item.updated = True
        item.save()

        # Updating Item's variants
        item.variants.clear()
        VariantOption.objects.filter(item=item).delete()
        if variants:
            self._get_or_create_variants_with_options(item, user, variants)

        register_activity(user, "updated", "item", [item.name])

        return item

    def to_representation(self, instance: Item):
        item_repr = super().to_representation(instance)
        item_repr['created_by'] = instance.created_by.username
        item_repr['category'] = instance.category.name if instance.category else None
        item_repr['price'] = float(instance.price)
        item_repr['total_price'] = float(instance.total_price) 
        item_repr['supplier'] = instance.supplier.name if instance.supplier else None
        item_repr['variants'] = self.get_variants(instance)
        item_repr['in_inventory'] = instance.in_inventory
        item_repr['created_at'] = date_repr_format(instance.created_at)
        item_repr['updated_at'] = date_repr_format(instance.updated_at)
        return item_repr
