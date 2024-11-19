from rest_framework import serializers
from django.db import transaction
from utils.serializers import (datetime_repr_format,
                               get_location,
                               get_or_create_location)
from ..client_orders.serializers import LocationSerializer
from .models import Supplier


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
