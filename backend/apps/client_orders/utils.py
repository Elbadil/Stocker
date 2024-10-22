from rest_framework import serializers
from typing import Union
from .models import Location, AcquisitionSource
from ..inventory.models import Item


def get_or_create_location(
        user,
        data,
    ) -> Union[Location, None]:
    from .serializers import LocationSerializer

    if data:
        serializer = LocationSerializer(data=data,
                                        context={'user': user})
        if serializer.is_valid():
            obj = serializer.save()
            return obj
        else:
            raise serializers.ValidationError(serializer.errors)
    return None


def get_or_create_source(
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


def get_location(instance_attribute):
    if instance_attribute:
        return {
            'country': instance_attribute.country,
            'region': instance_attribute.region,
            'city': instance_attribute.city,
            'street_address': instance_attribute.street_address,
        }
    return None
