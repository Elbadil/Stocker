from django.db.models import F
from .models import ClientOrder, ClientOrderedItem
from ..inventory.models import Item


def reset_client_ordered_items(instance: ClientOrder):
    prev_items = instance.items
    for ordered_item in prev_items:
        Item.objects.filter(id=ordered_item.item.id).update(
            quantity=F('quantity') + ordered_item.ordered_quantity
        )
    ClientOrderedItem.objects.filter(order=instance).delete()
