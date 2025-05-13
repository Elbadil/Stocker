from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from shortuuid.django_fields import ShortUUIDField
from decimal import Decimal
from utils.models import BaseModel, get_default_order_status
from ..inventory.models import Item
from ..client_orders.models import (Client,
                                    AcquisitionSource,
                                    Location,
                                    OrderStatus)


User = get_user_model()


class Sale(BaseModel):
    """Sale Model"""
    reference_id = ShortUUIDField(length=7,
                                  max_length=12,
                                  prefix="ID_")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='sales',
                                   help_text="The user who created this sale")
    client = models.ForeignKey(Client, on_delete=models.PROTECT,
                               null=True, related_name="sales",
                               help_text="The client this sale is associated with")
    delivery_status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT,
                                        related_name='sale_delivery_status',
                                        blank=True,
                                        default=get_default_order_status)
    payment_status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT,
                                       related_name='sale_payment_status',
                                       blank=True,
                                       default=get_default_order_status)
    source = models.ForeignKey(AcquisitionSource, on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name="sales",
                               help_text="The source through which this sale was acquired")
    shipping_address = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name="sales",
                                         help_text="The address to ship the items sold",)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True,
                                        blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    updated = models.BooleanField(default=False)

    @property
    def items(self):
        return self.sold_items.all()

    @property
    def total_quantity(self):
        return sum(item.sold_quantity for item in self.items)        

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items)

    @property
    def total_cost(self):
        items_cost = sum(item.total_cost for item in self.items)
        if self.shipping_cost:
            return items_cost + self.shipping_cost
        return items_cost

    @property
    def net_profit(self):
        return self.total_price - self.total_cost

    @property
    def has_order(self):
        return hasattr(self, 'order')

    @property
    def linked_order(self):
        return self.order.id if self.has_order else None

    def __str__(self):
        return self.reference_id


class SoldItem(BaseModel):
    """Sold Item Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, related_name='sold_items')
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE,
                             null=False, blank=True,
                             related_name='sold_items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    sold_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    sold_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )

    @property
    def total_price(self):
        return self.sold_quantity * self.sold_price

    @property
    def total_cost(self):
        return self.sold_quantity * self.item.price

    @property
    def total_profit(self):
        return self.total_price - self.total_cost

    @property
    def unit_profit(self):
        return self.sold_price - self.item.price

    def __str__(self):
        return self.item.name
