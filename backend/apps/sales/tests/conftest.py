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
def supplier(db, user):
    return SupplierFactory.create(created_by=user, name="Dell")

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
        sold_quantity=item.quantity - 1,
        sold_price=item.price + 100
    )

@pytest.fixture
def client_order(db, user, location, client, source, pending_status):
    return ClientOrderFactory.create(
        created_by=user,
        client=client,
        delivery_status=pending_status,
        payment_status=pending_status,
        shipping_address=location,
        source=source
    )

@pytest.fixture
def location_data(city, country):
    return {
        "country": country.name,
        "city": city.name,
        "street_address": "5th avenue"
    }

@pytest.fixture
def sale_data(user, client, item, pending_status, location_data, source):
    return {
        "client": client.name,
        "sold_items": [
            {
                "item": item.name,
                "sold_quantity": item.quantity - 1,
                "sold_price": item.price + 100
            }
        ],
        "delivery_status": pending_status.name,
        "payment_status": pending_status.name,
        "shipping_address": location_data,
        "source": source.name
    }

@pytest.fixture
def sold_item_data(item, sale):
    return {
        "sale": sale.id,
        "item": item.name,
        "sold_quantity": item.quantity - 1,
        "sold_price": item.price + 100
    }
