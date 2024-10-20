from rest_framework import serializers
from django.db import transaction
from typing import Union
from .models import Client, Location, AcquisitionSource


class LocationSerializer(serializers.ModelSerializer):
    """Location Serializer"""
    class Meta:
        model = Location
        fields = '__all__'

    def create(self, validated_data):
        user = self.context.get('user')
        lookup_data = {f"{k}__iexact": v for k, v in validated_data.items()}
        lookup_data['added_by'] = user

        location, created = Location.objects.get_or_create(
            **lookup_data,
            defaults=validated_data
        )

        return location


class AcquisitionSourceSerializer(serializers.ModelSerializer):
    """Acquisition Source Serializer"""
    class Meta:
        model = AcquisitionSource
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    """Client Serializer"""
    location = LocationSerializer(many=False, required=False)
    source = serializers.CharField(required=False)

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
            'created_at',
            'updated_at',
            'updated',
        ]

    def get_location(self, client: Client):
        if client.location:
            return {
                'country': client.location.country,
                'region': client.location.region,
                'city': client.location.city,
                'street_address': client.location.street_address,
            }
        return None

    def _get_or_create_location(
        self,
        user,
        data,
    ) -> Union[Location, None]:
        if data:
            serializer = LocationSerializer(data=data,
                                            context={'user': user})
            if serializer.is_valid():
                obj = serializer.save()
                return obj
            else:
                raise serializers.ValidationError(serializer.errors)
        return None

    def _get_or_create_source(
        self,
        user,
        value
    ) -> Union[AcquisitionSource, None]:
        if value:
            acq_source, created = AcquisitionSource.objects.get_or_create(
                added_by=user,
                name__iexact=value,
                defaults={'name': value}
            )
            return acq_source
        return None

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
        client.location = self._get_or_create_location(
            user,
            location
        )
        client.source = self._get_or_create_source(
            user,
            source
        )
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

        # Update client's location and source of acquisition
        client.location = self._get_or_create_location(
            user,
            location
        )
        client.source = self._get_or_create_source(
            user,
            source
        )
        client.updated = True
        client.save()

        return client

    def to_representation(self, instance: Client):
        client_repr = super().to_representation(instance)
        client_repr['created_by'] = instance.created_by.username
        client_repr['location'] = self.get_location(instance)
        client_repr['source'] = instance.source.name if instance.source else None
        client_repr['created_at'] = instance.created_at.strftime('%d/%m/%Y')
        client_repr['updated_at'] = instance.updated_at.strftime('%d/%m/%Y')
        return client_repr
