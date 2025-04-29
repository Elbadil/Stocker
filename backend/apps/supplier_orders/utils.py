from rest_framework.exceptions import NotFound
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from ..base.models import User
from ..inventory.models import Item
from .models import SupplierOrder, SupplierOrderedItem


def validate_supplier_order(order_id: UUID, user: User):
    order = SupplierOrder.objects.filter(id=order_id, created_by=user).first()
    if not order:
        raise NotFound(f"Order with id '{order_id}' does not exist.")
    return order

def average_price(item: Item, ordered_item: SupplierOrderedItem):
    total_quantity = item.quantity + ordered_item.ordered_quantity
    av_price = (item.total_price + ordered_item.total_price) / total_quantity
    return av_price.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
