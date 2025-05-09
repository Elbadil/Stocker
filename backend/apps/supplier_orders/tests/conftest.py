import pytest
import uuid
from rest_framework.test import APIClient
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
def random_uuid():
    return str(uuid.uuid4())

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

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
def supplier_data(location):
    return {
        "name": "Supplier 1",
        "location": {
            "country": location.country.name,
            "city": location.city.name,
            "street_address": location.street_address
        }
    }

@pytest.fixture
def supplier(db, user):
    return SupplierFactory.create(created_by=user)

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
def item_2(db, user, supplier):
    return ItemFactory.create(
        created_by=user,
        supplier=supplier,
        name="Pack",
        quantity=5,
        in_inventory=True
    )

@pytest.fixture
def order_data(supplier, pending_status):
    return {
        "supplier": supplier.name,
        "delivery_status": pending_status.name,
        "payment_status": pending_status.name,
        "ordered_items": [
            {
                "item": "Projector",
                "ordered_quantity": 5,
                "ordered_price": 640
            }
        ]
    }

@pytest.fixture
def supplier_order(db, user, pending_status, supplier):
    return SupplierOrderFactory.create(
        created_by=user,
        supplier=supplier,
        delivery_status=pending_status,
        payment_status=pending_status,
    )

@pytest.fixture
def location_data(city, country):
    return {
        "country": country.name,
        "city": city.name,
        "street_address": "5th avenue"
    }

@pytest.fixture
def ordered_item_data(supplier_order, supplier):
    return {
        "order": supplier_order.id,
        "supplier": supplier.name,
        "item": "DataShow",
        "ordered_quantity": 5,
        "ordered_price": 640
    }

@pytest.fixture
def ordered_item(db, user, supplier_order, supplier, item):
    return SupplierOrderedItemFactory.create(
        created_by=user,
        order=supplier_order,
        supplier=supplier,
        item=item
    )

@pytest.fixture
def ordered_item_2(db, user, supplier_order, supplier, item_2):
    return SupplierOrderedItemFactory.create(
        created_by=user,
        order=supplier_order,
        supplier=supplier,
        item=item_2
    )
