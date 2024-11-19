from rest_framework import serializers
from django.db.models import F
from typing import Union
from .models import (Location,
                     AcquisitionSource,
                     ClientOrder,
                     ClientOrderedItem)
from ..inventory.models import Item


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


def reset_client_ordered_items(instance: ClientOrder):
    prev_items = instance.items
    for ordered_item in prev_items:
        Item.objects.filter(id=ordered_item.item.id).update(
            quantity=F('quantity') + ordered_item.ordered_quantity
        )
    ClientOrderedItem.objects.filter(order=instance).delete()
