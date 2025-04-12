import factory
from apps.base.factories import UserFactory
from apps.sales.models import Sale
from apps.client_orders.factories import (
    ClientFactory,
    OrderStatusFactory,
    AcquisitionSourceFactory,
    LocationFactory,
)

class SaleFactory(factory.django.DjangoModelFactory):
    """Sale factory"""
    class Meta:
        model = Sale

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
    