import factory
from apps.base.factories import UserFactory
from apps.client_orders.factories import LocationFactory, OrderStatusFactory
from .models import Supplier, SupplierOrder, SupplierOrderedItem


class SupplierFactory(factory.django.DjangoModelFactory):
    """Supplier Factory"""
    class Meta:
        model = Supplier

    created_by = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"supplier_{n}")
    phone_number = factory.Faker("phone_number")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.name.replace(' ', '.').lower()}@example.com"
    )
    location = factory.SubFactory(LocationFactory)


class SupplierOrderFactory(factory.django.DjangoModelFactory):
    """Supplier Order Factory"""
    class Meta:
        model = SupplierOrder

    created_by = factory.SubFactory(UserFactory)
    supplier = factory.SubFactory(SupplierFactory)
    delivery_status = factory.SubFactory(OrderStatusFactory)
    payment_status = factory.SubFactory(OrderStatusFactory)
    tracking_number = factory.Faker('ean')
    shipping_cost = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=199.99,
        min_value=5,
    )


class SupplierOrderedItemFactory(factory.django.DjangoModelFactory):
    """Supplier Ordered Item Factory"""
    class Meta:
        model = SupplierOrderedItem

    created_by = factory.SubFactory(UserFactory)
    order = factory.SubFactory(SupplierOrderFactory)
    item = factory.SubFactory("apps.inventory.factories.ItemFactory")
    ordered_quantity = factory.Faker("pyint", min_value=1, max_value=20)
    ordered_price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=999.99,
        min_value=1,
    )
