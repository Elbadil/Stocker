from ..inventory.models import Item
from .models import SupplierOrderedItem

def average_price(item: Item, ordered_item: SupplierOrderedItem):
    total_quantity = item.quantity + ordered_item.ordered_quantity
    return (item.total_price + ordered_item.total_price) / total_quantity
