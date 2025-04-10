from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from shortuuid.django_fields import ShortUUIDField
from utils.models import BaseModel, get_default_order_status
from ..client_orders.models import Location, OrderStatus


User = get_user_model()


class Supplier(BaseModel):
    """Supplier Model"""
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_suppliers',
        null=True,
        blank=True,
        help_text="The user who initially registered this supplier"
    )
    name = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    updated = models.BooleanField(default=False)

    @property
    def total_items(self):
        return self.items.all().count()

    @property
    def total_orders(self):
        return self.orders.all().count()

    def __str__(self) -> str:
        return self.name


class SupplierOrder(BaseModel):
    """Supplier Order Model"""
    reference_id = ShortUUIDField(length=7, max_length=12, prefix="ID_")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_supplier_orders',
        help_text="The user who created this order",
        null=True,
        blank=True
    )
    supplier = models.ForeignKey(Supplier,
                                 on_delete=models.PROTECT, null=True,
                                 related_name='orders')
    delivery_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.SET_NULL,
        related_name="supplier_delivery_status",
        null=True, blank=True,
        default=get_default_order_status
    )
    payment_status = models.ForeignKey(
        OrderStatus, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="supplier_payment_status",
        default=get_default_order_status
    )
    tracking_number = models.CharField(max_length=50,
                                       null=True,
                                       blank=True,
                                       help_text="Tracking number for the shipment")
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True, blank=True)
    updated = models.BooleanField(default=False)

    @property
    def items(self):
        return self.ordered_items.all()

    @property
    def total_quantity(self):
        return sum(item.ordered_quantity for item in self.items)

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items)

    def __str__(self) -> str:
        return self.reference_id


class SupplierOrderedItem(BaseModel):
    """Supplier Ordered Item Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, blank=True)
    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name="ordered_items")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True,
                                 related_name='ordered_items')
    item = models.ForeignKey('inventory.Item', on_delete=models.PROTECT,
                             null=True, blank=True)
    ordered_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    ordered_price = models.DecimalField(max_digits=6, decimal_places=2)

    @property
    def in_inventory(self):
        return self.item.in_inventory

    @property
    def total_price(self):
        return self.ordered_quantity * self.ordered_price

    def __str__(self) -> str:
        return self.item.name
