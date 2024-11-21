from rest_framework import serializers
from typing import Union
from apps.client_orders.models import Location


DELIVERY_STATUS_OPTIONS = [
    'pending',
    'shipped',
    'delivered',
    'returned',
    'canceled',
    'failed'
]

PAYMENT_STATUS_OPTIONS = [
    'pending',
    'paid',
    'failed',
    'refunded'
]

def datetime_repr_format(datetime):
    """Returns the correct format for datetime data representation"""
    return datetime.strftime('%d/%m/%Y')


def get_or_create_location(
        user,
        data,
    ) -> Union[Location, None]:
    """Handles location creation"""
    from apps.client_orders.serializers import LocationSerializer

    if data:
        serializer = LocationSerializer(data=data,
                                        context={'user': user})
        if serializer.is_valid():
            obj = serializer.save()
            return obj
        else:
            raise serializers.ValidationError(serializer.errors)
    return None


def get_location(instance_attribute):
    """Returns the correct format for location data representation"""
    if instance_attribute:
        return {
            'country': instance_attribute.country.name,
            'city': instance_attribute.city.name,
            'street_address': instance_attribute.street_address,
        }
    return None