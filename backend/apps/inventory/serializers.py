from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError
import json
from typing import Union
from ..base.models import User
from .models import Item, Category, Supplier, Variant, VariantOption


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""
    class Meta:
        model = Category
        fields = "__all__"


class SupplierSerializer(serializers.ModelSerializer):
    """Supplier Serializer"""
    class Meta:
        model = Supplier
        fields = "__all__"


class VariantOptionSerializer(serializers.ModelSerializer):
    """Variant Serializer"""
    class Meta:
        model = VariantOption
        fields = "__all__"


class VariantSerializer(serializers.ModelSerializer):
    """Variant Serializer"""
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
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

    class Meta:
        model = Item
        fields = [
            'id',
            'user',
            'category',
            'supplier',
            'name',
            'quantity',
            'price',
            'total_price',
            'picture',
            'variants',
            'created_at',
            'updated_at',
            'updated',
        ]

    def get_variants(self, item: Item):
        variants = []
        for variant in item.variants.all():
            variant_options = VariantOption.objects.filter(variant=variant, item=item)
            variants.append({'name': variant.name,
                             'options': [option.body for option in variant_options]})
        return variants if len(variants) > 0 else None

    def validate_name(self, value):
        user = self.context.get('request').user
        if Item.objects.filter(
            user=user,
            name__iexact=value).exclude(pk=self.instance.id
                                        if self.instance
                                        else None).exists():
            raise ValidationError('Item with this name already exists.')
        return value

    def _get_or_create_category_supplier(
        self, 
        user: User, 
        model: Union[Category, Supplier],
        value: str
    ) -> Union[None, Category, Supplier]:
        if value:
            obj, created = model.objects.get_or_create(
                user=user,
                name__iexact=value,
                defaults={'name': value})
            return obj
        return None

    def validate_variants(self, value):
        try:
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

            return variants
        except json.JSONDecodeError:
            raise serializers.ValidationError("Invalid JSON format for variants.")

    def _get_or_create_variants_with_options(
        self, 
        item: Item, 
        user: User, 
        variants: list
    ) -> None:
        for variant_data in variants:
            variant_name = variant_data.get('name')
            options = variant_data.get('options', [])
            print(f"Processing variant: {variant_name} with options: {options}")
            # Getting or creating variant
            variant, created = Variant.objects.get_or_create(
                name__iexact=variant_name,
                defaults={'name': variant_name},
                user=user
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


    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get('request').user
        variants = validated_data.pop('variants', [])
        category_name = validated_data.pop('category', None)
        supplier_name = validated_data.pop('supplier', None)

        # Creating Item's main fields
        item = Item.objects.create(user=user, **validated_data)

        # Creating Item's category and supplier
        item.category = self._get_or_create_category_supplier(user, Category, category_name)
        item.supplier = self._get_or_create_category_supplier(user, Supplier, supplier_name)
        item.save()

        # Creating and Adding Item's variants with options
        self._get_or_create_variants_with_options(item, user, variants)
        return item

    @transaction.atomic
    def update(self, instance: Item, validated_data):
        variants = validated_data.pop('variants', [])
        category_name = validated_data.pop('category', None)
        supplier_name = validated_data.pop('supplier', None)

        # Updating Item's main fields
        item = super().update(instance, validated_data)
        user = self.context.get('request').user

        # Updating Item's category and supplier
        item.category = self._get_or_create_category_supplier(user, Category, category_name)
        item.supplier = self._get_or_create_category_supplier(user, Supplier, supplier_name)
        item.updated = True
        item.save()

        # Updating Item's variants
        item.variants.clear()
        VariantOption.objects.filter(item=item).delete()
        self._get_or_create_variants_with_options(item, user, variants)

        return item

    def to_representation(self, instance: Item):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.username
        representation['category'] = instance.category.name if instance.category else None
        representation['supplier'] = instance.supplier.name if instance.supplier else None
        representation['variants'] = self.get_variants(instance)
        representation['created_at'] = instance.created_at.strftime('%d/%m/%Y')
        representation['updated_at'] = instance.created_at.strftime('%d/%m/%Y')
        return representation
