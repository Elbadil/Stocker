import factory
import random
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from utils.status import ORDER_STATUS
from .models import (
    Country,
    City,
    Location,
    AcquisitionSource,
    Client,
    OrderStatus,
    ClientOrder,
    ClientOrderedItem
)


class CountryFactory(factory.django.DjangoModelFactory):
    """Country Factory"""
    class Meta:
        model = Country

    name = factory.Sequence(lambda n: f"country_{n}")


class CityFactory(factory.django.DjangoModelFactory):
    """City Factory"""
    class Meta:
        model = City

    country = factory.SubFactory(CountryFactory)
    name = factory.Sequence(lambda n: f"city_{n}")


class LocationFactory(factory.django.DjangoModelFactory):
    """Location Factory"""
    class Meta:
        model = Location

    added_by = factory.SubFactory(UserFactory)
    country = factory.SubFactory(CountryFactory)
    city = factory.SubFactory(CityFactory)
    street_address = factory.Faker("address")


class AcquisitionSourceFactory(factory.django.DjangoModelFactory):
    """Acquisition Source Factory"""
    class Meta:
        model = AcquisitionSource

    added_by = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"source_{n}")


class ClientFactory(factory.django.DjangoModelFactory):
    """Client Factory"""
    class Meta:
        model = Client

    name = factory.Sequence(lambda n: f"client_{n}")
    age = factory.Faker("pyint", min_value=15, max_value=80)
    phone_number = factory.Faker("phone_number")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.name.replace(' ', '.').lower()}@example.com"
    )
    sex = factory.Faker("random_element", elements=["Male", "Female"])
    location = factory.SubFactory(LocationFactory)
    source = factory.SubFactory(AcquisitionSourceFactory)


class OrderStatusFactory(factory.django.DjangoModelFactory):
    """Order Status Factory"""
    class Meta:
        model = OrderStatus

    name = factory.Sequence(lambda n: f"{random.choice(ORDER_STATUS)}_{n}")


class ClientOrderFactory(factory.django.DjangoModelFactory):
    """Client Order Factory"""
    class Meta:
        model = ClientOrder
    
    created_by = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)
    delivery_status = factory.SubFactory(OrderStatusFactory)
    payment_status = factory.SubFactory(OrderStatusFactory)
    tracking_number = factory.Faker('ean')
    shipping_address = factory.SubFactory(LocationFactory)
    shipping_cost = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=199.99,
        min_value=5,
    )
    source = factory.SubFactory(AcquisitionSourceFactory)


class ClientOrderedItemFactory(factory.django.DjangoModelFactory):
    """Client Ordered Item Factory"""
    class Meta:
        model = ClientOrderedItem

    created_by = factory.SubFactory(UserFactory)
    order = factory.SubFactory(ClientOrderFactory)
    item = factory.SubFactory(ItemFactory)
    ordered_quantity = factory.Faker("pyint", min_value=1, max_value=20)
    ordered_price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=999.99,
        min_value=1,
    )
