from rest_framework import serializers
from typing import Any, Union, Optional, Callable
from apps.base.models import User
from apps.client_orders.models import Location

def datetime_repr_format(datetime):
    """Returns the correct format for datetime data representation"""
    return datetime.strftime('%d/%m/%Y')


def get_or_create_location(
    user: User,
    data: dict,
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


def handle_null_fields(fields: dict):
    """Sets frontend FormData object's null field values to None"""
    for key, value in fields.items():
        if value == 'null':
            fields[key] = None
    return fields


def update_field(
    self,
    instance,
    field_name: str,
    value: Optional[Any],
    create_func: Optional[Callable] = None,
    user: Optional[User] = None
):
    """Updates instance field value with optional creation function"""
    if value:
        if create_func and user:
            setattr(instance, field_name, create_func(user, value))
        else:
            setattr(instance, field_name, value)
    elif field_name in self.initial_data:
        setattr(instance, field_name, None)
