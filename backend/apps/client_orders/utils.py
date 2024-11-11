from rest_framework import serializers
from django.db.models import F
from typing import Union
from .models import Location, AcquisitionSource, Order, OrderedItem
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
            added_by__isnull=True,
            name__iexact=value,
            defaults={'added_by': user,
                      'name': value}
        )
        return acq_source
    return None


def get_location(instance_attribute):
    if instance_attribute:
        return {
            'country': instance_attribute.country.name,
            'city': instance_attribute.city.name,
            'street_address': instance_attribute.street_address,
        }
    return None


def reset_ordered_items(instance: Order):
    prev_items = instance.items
    for ordered_item in prev_items:
        Item.objects.filter(id=ordered_item.item.id).update(
            quantity=F('quantity') + ordered_item.ordered_quantity
        )
    OrderedItem.objects.filter(order=instance).delete()
