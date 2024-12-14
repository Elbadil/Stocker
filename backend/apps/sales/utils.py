from django.db.models import F
from ..inventory.models import Item
from .models import Sale

def reset_sale_sold_items(instance: Sale):
    sold_items = instance.items
    for sold_item in sold_items:
        Item.objects.filter(id=sold_item.item.id).update(
            quantity=F('quantity') + sold_item.sold_quantity
        )
  