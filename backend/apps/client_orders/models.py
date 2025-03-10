from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from shortuuid.django_fields import ShortUUIDField
from decimal import Decimal
from utils.models import BaseModel


User = get_user_model()


class Country(BaseModel):
    """Country Model"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class City(BaseModel):
    """City Model"""
    country = models.ForeignKey(Country, on_delete=models.CASCADE,
                                related_name='cities')
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ['name', 'country']

    def __str__(self) -> str:
        return f'{self.name}, {self.country.name}'


class Location(BaseModel):
    """Location Model"""
    added_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='added_locations',
                                 help_text="The user who added this location to the system",
                                 null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL,
                                null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL,
                             null=True, blank=True)
    street_address = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self) -> str:
        components = []
        if self.street_address:
            components.append(self.street_address)
        if self.city:
            components.append(self.city.name)
        if self.country:
            components.append(self.country.name)
        if self.added_by:
            return ', '.join(components) + f' added by: {self.added_by.username}'
        return ', '.join(components)


class AcquisitionSource(BaseModel):
    """Acquisition Source Model"""
    added_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='added_acquisition_sources',
                                 help_text="The user who added this acquisition source to the system",
                                 null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        if self.added_by:
            return f'{self.name} added by: {self.added_by.username}'
        return self.name


class Client(BaseModel):
    """Client Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='created_clients',
                                   help_text="The user who initially registered this client",
                                   null=True,
                                   blank=True)
    name = models.CharField(max_length=100, unique=True)
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True,
                           choices=[('Male', 'Male'),
                                     ('Female', 'Female')])
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    source = models.ForeignKey(AcquisitionSource,
                               on_delete=models.SET_NULL,
                               related_name='acquired_clients',
                               help_text="The source through which this client was acquired",
                               null=True,
                               blank=True)
    updated = models.BooleanField(default=False)

    @property
    def total_orders(self):
        return self.orders.all().count()

    def __str__(self) -> str:
        return self.name


class OrderStatus(BaseModel):
    """Order Status Model"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class ClientOrder(BaseModel):
    """Client Order Model"""
    reference_id = ShortUUIDField(length=7,
                                  max_length=12,
                                  prefix="ID_")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='created_client_orders',
                                   help_text="The user who created this order",
                                   null=True,
                                   blank=True)
    sale = models.OneToOneField('sales.Sale', on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='order')
    client = models.ForeignKey(Client, on_delete=models.PROTECT,
                               related_name="orders",
                               null=True)
    delivery_status = models.ForeignKey(OrderStatus, on_delete=models.SET_NULL,
                                        related_name='client_delivery_status',
                                        null=True, blank=True,
                                        default="8ccdc2f8-1d6e-489f-81cf-7df3c4fce245")
    payment_status = models.ForeignKey(OrderStatus, on_delete=models.SET_NULL,
                                       related_name='client_payment_status',
                                       null=True, blank=True,
                                       default="8ccdc2f8-1d6e-489f-81cf-7df3c4fce245")
    tracking_number = models.CharField(max_length=50, null=True, blank=True,
                                       help_text="Tracking number for the shipment")
    shipping_address = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                         null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True, blank=True)
    source = models.ForeignKey(AcquisitionSource,
                               on_delete=models.SET_NULL,
                               related_name='acquired_orders',
                               help_text="The source through which this order was acquired",
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

    @property
    def net_profit(self):
        return self.total_price - self.shipping_cost if self.shipping_cost else self.total_price

    @property
    def linked_sale(self):
        return self.sale.reference_id if self.sale else None

    def __str__(self) -> str:
        return self.reference_id


class ClientOrderedItem(BaseModel):
    """Ordered Item Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, blank=True)
    order = models.ForeignKey(ClientOrder, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name="ordered_items")
    item = models.ForeignKey('inventory.Item', on_delete=models.PROTECT)
    ordered_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    ordered_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )

    @property
    def total_price(self):
        return self.ordered_quantity * self.ordered_price

    @property
    def total_profit(self):
        return (
            (self.ordered_price * self.ordered_quantity) -
            (self.ordered_quantity * self.item.price)
        )

    @property
    def unit_profit(self):
        return (self.total_price / self.ordered_quantity) - self.item.price

    def __str__(self) -> str:
        return f'{self.order.client.name} ordered {self.ordered_quantity} of {self.item.name}'

    class Meta:
        ordering = ['created_at']
