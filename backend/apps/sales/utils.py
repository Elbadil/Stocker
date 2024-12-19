from django.db.models import F
from rest_framework.exceptions import NotFound
from typing import List
from uuid import UUID
from ..base.models import User
from ..inventory.models import Item
from .models import Sale, SoldItem


def validate_sale(sale_id: UUID, user: User):
    sale = Sale.objects.filter(id=sale_id, created_by=user).first()
    if not sale:
        raise NotFound(f"Sale with id '{sale_id}' does not exist.")
    return sale

def reset_sold_items(sold_items: List[SoldItem]):
    for sold_item in sold_items:
        Item.objects.filter(id=sold_item.item.id).update(
            quantity=F('quantity') + sold_item.sold_quantity
        )
