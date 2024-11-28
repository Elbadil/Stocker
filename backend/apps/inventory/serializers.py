from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError
import json
from utils.serializers import handle_null_fields, update_field
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
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        required=False
    )
    name = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Variant
        fields = "__all__"

    def create(self, validated_data):
        variant_options = validated_data.pop('options', [])
        variant, created = Variant.objects.get_or_create(
            name__iexact=validated_data['name'],
            **validated_data
        )
        item = self.context.get('item')
        unique_options = set([option.lower() for option in variant_options])
        for option in variant_options:
            if option.lower() in unique_options:
                unique_options.remove(option.lower())
                VariantOption.objects.create(
                    item=item,
                    variant=variant,
                    body=option)
        return variant


class ItemSerializer(serializers.ModelSerializer):
    """Item Serializer"""
    category = serializers.CharField(allow_blank=True, required=False)
    supplier = serializers.CharField(allow_blank=True, required=False)
    price = serializers.FloatField()
    variants = serializers.CharField(write_only=True, required=False)
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
            options = variant_data.get('options', [])

            # Getting or creating variant
            variant, created = Variant.objects.get_or_create(
                name__iexact=variant_name,
                defaults={'name': variant_name},
                created_by=user
            )

            # Adding variant to item's variants
            item.variants.add(variant)

            # Creating variant options
            for option in options:
                VariantOption.objects.create(
                    item=item,
                    variant=variant,
                    body=option
                )

    def validate_name(self, value):
        user = self.context.get('request').user
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
            user = self.context.get('request').user
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
                    if variant['name'] in unique_variants:
                        raise serializers.ValidationError("Each variant name should be unique.")
                    unique_variants.append(variant['name'])

                return variants
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format for variants.")
        return None

    def validate(self, attrs):
        return handle_null_fields(attrs)

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get('request').user
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

        return item

    @transaction.atomic
    def update(self, instance: Item, validated_data):
        variants = validated_data.pop('variants', None)
        category_name = validated_data.pop('category', None)
        supplier = validated_data.pop('supplier', None)

        # Updating Item's main fields
        item = super().update(instance, validated_data)
        user = self.context.get('request').user

        # Updating Item's category
        update_field(item,
                     'category',
                      category_name,
                      self._get_or_create_category,
                      user)

        # Updating Item's supplier
        update_field(item, 'supplier', supplier)

        item.updated = True
        item.save()

        # Updating Item's variants
        item.variants.clear()
        VariantOption.objects.filter(item=item).delete()
        if variants:
            self._get_or_create_variants_with_options(item, user, variants)

        return item

    def to_representation(self, instance: Item):
        representation = super().to_representation(instance)
        representation['created_by'] = instance.created_by.username
        representation['category'] = instance.category.name if instance.category else None
        representation['supplier'] = instance.supplier.name if instance.supplier else None
        representation['variants'] = self.get_variants(instance)
        representation['created_at'] = instance.created_at.strftime('%d/%m/%Y')
        representation['updated_at'] = instance.updated_at.strftime('%d/%m/%Y')
        return representation
