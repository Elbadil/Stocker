from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from utils.models import BaseModel
from ..inventory.models import Item


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
        components = [self.city.name]
        if self.street_address:
            components.append(self.street_address)
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

    class Meta:
        ordering = ['-created_at']

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


class Order(BaseModel):
    """Order Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='created_orders',
                                   help_text="The user who created this order",
                                   null=True,
                                   blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL,
                               related_name="orders",
                               null=True)
    status = models.ForeignKey(OrderStatus, on_delete=models.SET_NULL,
                               null=True, blank=True,
                               default="8ccdc2f8-1d6e-489f-81cf-7df3c4fce245")
    shipping_address = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                         null=True)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2,
                                        null=True, blank=True)
    source = models.ForeignKey(AcquisitionSource,
                               on_delete=models.SET_NULL,
                               related_name='acquired_orders',
                               help_text="The source through which this order was acquired",
                               null=True)
    updated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

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
    def total_profit(self):
        return sum(item.total_profit for item in self.items) - self.shipping_cost

    def __str__(self) -> str:
        return f'Order by: {self.client.name}'


class OrderedItem(BaseModel):
    """Ordered Item Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                   null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              null=True, blank=True,
                              related_name="ordered_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    ordered_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    ordered_price = models.DecimalField(max_digits=6, decimal_places=2)

    @property
    def total_price(self):
        return self.ordered_quantity * self.ordered_price

    @property
    def total_profit(self):
        return self.ordered_price - (self.ordered_quantity * self.item.price)

    @property
    def unit_profit(self):
        return (self.total_price / self.ordered_quantity) - self.item.price

    def __str__(self) -> str:
        return f'{self.order.client.name} ordered {self.ordered_quantity} of {self.item.name}'
