import pytest
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.client_orders.factories import (
    ClientFactory,
    ClientOrderFactory,
    CountryFactory,
    CityFactory,
    LocationFactory,
    OrderStatusFactory,
    AcquisitionSourceFactory
)
from apps.supplier_orders.factories import SupplierFactory
from apps.sales.factories import SaleFactory, SoldItemFactory


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
def supplier(db, user, location):
    return SupplierFactory.create(created_by=user, name="Dell", location=location)

@pytest.fixture
def item(db, user, supplier):
    return ItemFactory.create(
        created_by=user,
        supplier=supplier,
        name="Projector",
        quantity=5,
        in_inventory=True
    )

@pytest.fixture
def pending_status(db):
    return OrderStatusFactory.create(name="Pending")

@pytest.fixture
def delivered_status(db):
    return OrderStatusFactory.create(name="Delivered")

@pytest.fixture
def source(db, user):
    return AcquisitionSourceFactory.create(name="ADS", added_by=user)

@pytest.fixture
def client(db, user, location, source):
    return ClientFactory.create(
        name="Haitam",
        created_by=user,
        location=location,
        source=source,
    )

@pytest.fixture
def sale(db, user, location, client, source, pending_status):
    return SaleFactory.create(
        created_by=user,
        client=client,
        delivery_status=pending_status,
        payment_status=pending_status,
        shipping_address=location,
        source=source,
    )

@pytest.fixture
def sold_item(db, user, sale, item):
    return SoldItemFactory.create(
        created_by=user,
        sale=sale,
        item=item,
        ordered_quantity=item.quantity - 1,
        ordered_price=item.price + 100
    )

@pytest.fixture
def client_order(db, sale):
    order_data = {
        field: getattr(sale, field)
        for field in [
            "created_by",
            "client",
            "delivery_status",
            "payment_status",
            "shipping_address",
            "shipping_cost",
            "source",
            "tracking_number",
        ]
    }
    return ClientOrderFactory.create(**order_data)
