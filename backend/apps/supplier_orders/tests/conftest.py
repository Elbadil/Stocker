import pytest
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderFactory,
    SupplierOrderedItemFactory
)
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.client_orders.factories import (
    CountryFactory,
    CityFactory,
    LocationFactory,
    OrderStatusFactory
)


@pytest.fixture
def user(db):
  return UserFactory.create(username="adel")

@pytest.fixture
def country(db):
    return CountryFactory.create(name="Morocco")

@pytest.fixture
def city(db, country):
    return CityFactory.create(country=country, name="Tetouan")

@pytest.fixture
def location(db, user, country, city):
    return LocationFactory.create(
        added_by=user,
        country=country,
        city=city,
        street_address="5th avenue"
    )

@pytest.fixture
def pending_status(db):
    return OrderStatusFactory.create(name="Pending")

@pytest.fixture
def delivered_status(db):
    return OrderStatusFactory.create(name="Delivered")

@pytest.fixture
def item(db, user):
    return ItemFactory.create(
        created_by=user,
        name="Projector",
        quantity=5,
        in_inventory=True
    )

@pytest.fixture
def supplier(db, user):
    return SupplierFactory.create(created_by=user)

@pytest.fixture
def supplier_order(db, user, pending_status, supplier):
    return SupplierOrderFactory.create(
        created_by=user,
        supplier=supplier,
        delivery_status=pending_status,
        payment_status=pending_status,
    )
