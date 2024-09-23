from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import ValidationError
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
    variants = VariantSerializer(many=True, required=False)

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

    def _get_or_create(self, user: User, model: Union[Category, Supplier], value):
        if value:
            obj, created = model.objects.get_or_create(
                user=user,
                name=value,
                defaults={'name': value})
            return obj
        return None

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get('request').user
        variants = validated_data.pop('variants', [])
        category_name = validated_data.pop('category', None)
        supplier_name = validated_data.pop('supplier', None)

        # Creating Item's main fields
        item = Item.objects.create(user=user, **validated_data)

        # Creating Item's category and supplier
        item.category = self._get_or_create(user, Category, category_name)
        item.supplier = self._get_or_create(user, Supplier, supplier_name)
        item.save()

        # Creating Item's variants
        errors = []
        for variant_data in variants:
            variant_data['user_id'] = user.id
            variant_serializer = VariantSerializer(data=variant_data,
                                                   context={'item': item})
            if variant_serializer.is_valid():
                variant = variant_serializer.save()
                item.variants.add(variant)
            else:
                errors.append(variant_serializer.errors)
        if errors:
            raise serializers.ValidationError(errors)

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
        item.category = self._get_or_create(user, Category, category_name)
        item.supplier = self._get_or_create(user, Supplier, supplier_name)
        item.save()

        # Updating Item's variants
        item.variants.clear()
        VariantOption.objects.filter(item=item).delete()
        errors = []
        for variant_data in variants:
            variant_data['user_id'] = user.id
            variant_serializer = VariantSerializer(data=variant_data,
                                                   context={'item': item})
            if variant_serializer.is_valid():
                variant = variant_serializer.save()
                item.variants.add(variant)
            else:
                errors.append(variant_serializer.errors)
        if errors:
            raise serializers.ValidationError(errors)

        return item

    def to_representation(self, instance: Item):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.username
        representation['category'] = instance.category.name if instance.category else None
        representation['supplier'] = instance.supplier.name if instance.supplier else None
        representation['variants'] = self.get_variants(instance)
        representation['created_at'] = instance.created_at.strftime('%m/%d/%Y')
        representation['updated_at'] = instance.created_at.strftime('%m/%d/%Y')
        return representation
