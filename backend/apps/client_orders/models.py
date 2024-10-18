from django.db import models
from django.core.validators import MinValueValidator
from utils.models import BaseModel
from ..inventory.models import Item


class Location(BaseModel):
    """Location Model"""
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        components = [self.city]
        if self.address:
            components.append(self.address)
        elif self.region:
            components.append(self.region)
        if self.country:
            components.append(self.country)
        return ', '.join(components)


class AcquisitionSource(BaseModel):
    """Acquisition Source Model"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Client(BaseModel):
    """Client Model"""
    name = models.CharField(max_length=100, unique=True)
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=10, null=True, blank=True,
                           choices=[('Male', 'Male'),
                                    ('Female', 'Female')])
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                 null=True)
    source_of_acquisition = models.ForeignKey(AcquisitionSource,
                                              on_delete=models.SET_NULL,
                                              null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class OrderStatus(BaseModel):
    """Order Status Model"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class Order(BaseModel):
    """Order Model"""
    client = models.ForeignKey(Client, on_delete=models.SET_NULL,
                               null=True)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL,
                             null=True)
    sold_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    sold_price = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.ForeignKey(OrderStatus, on_delete=models.SET_NULL,
                               null=True, blank=True)
    shipping_address = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                         null=True)
    source = models.ForeignKey(AcquisitionSource,
                               on_delete=models.SET_NULL,
                               null=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_sold_price(self):
        return self.sold_quantity * self.sold_price

    @property
    def total_profit(self):
        return self.total_sold_price - (self.sold_quantity * self.item.price)

    @property
    def unit_profit(self):
        return (self.total_sold_price / self.sold_quantity) - self.item.price

    def __str__(self) -> str:
        return f'{self.client.name} ordered {self.sold_quantity} of {self.item.name}'
