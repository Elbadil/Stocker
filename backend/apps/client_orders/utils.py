from django.db.models import F
from rest_framework.exceptions import NotFound
from typing import List
from uuid import UUID
from .models import ClientOrder, ClientOrderedItem
from ..base.models import User
from ..inventory.models import Item


def validate_client_order(order_id: UUID, user: User):
    order = ClientOrder.objects.filter(id=order_id, created_by=user).first()
    if not order:
        raise NotFound(f"Order with id '{order_id}' does not exist.")
    return order

def reset_client_ordered_items(ordered_items: List[ClientOrderedItem]):
    for ordered_item in ordered_items:
        Item.objects.filter(id=ordered_item.item.id).update(
            quantity=F('quantity') + ordered_item.ordered_quantity
        )
