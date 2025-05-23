import pytest
import uuid
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.client_orders.factories import (
    CountryFactory,
    CityFactory,
    LocationFactory,
    AcquisitionSourceFactory,
    ClientFactory,
    OrderStatusFactory,
    ClientOrderFactory,
    ClientOrderedItemFactory,
)
from apps.sales.factories import SaleFactory


@pytest.fixture
def user(db):
    return UserFactory.create(username="adel")

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def access_token(db, user):
    from rest_framework_simplejwt.tokens import AccessToken
    return AccessToken.for_user(user)

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def random_uuid():
    return str(uuid.uuid4())

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
def source(db, user):
    return AcquisitionSourceFactory.create(name="ADS", added_by=user)

@pytest.fixture
def client(db, user, location, source):
    return ClientFactory.create(
        name="Haitam",
        created_by=user,
        location=location,
        source=source
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
def client_order(db, user, client, location, source, pending_status):
    return ClientOrderFactory.create(
        created_by=user,
        client=client,
        shipping_address=location,
        source=source,
        delivery_status=pending_status,
        payment_status=pending_status,
    )

@pytest.fixture
def sale(db, client_order):
    sale_data = {
        field: getattr(client_order, field)
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
    return SaleFactory.create(**sale_data)

@pytest.fixture
def ordered_item(db, user, client_order, item):
    return ClientOrderedItemFactory.create(
        created_by=user,
        order=client_order,
        item=item,
        ordered_quantity=3,
        ordered_price=item.price + 100
    )

@pytest.fixture
def location_data(city, country):
    return {
        "country": country.name,
        "city": city.name,
        "street_address": "5th avenue"
    }

@pytest.fixture
def ordered_item_data(item, client_order):
    return {
        "order": client_order.id,
        "item": item.name,
        "ordered_quantity": item.quantity - 1,
        "ordered_price": item.price + 100
    }

@pytest.fixture
def order_data(
    client,
    ordered_item_data,
    pending_status,
    location_data,
    source
):
    return {
        "client": client.name,
        "ordered_items": [ordered_item_data],
        "delivery_status": pending_status.name,
        "payment_status": pending_status.name,
        "shipping_address": location_data,
        "source": source.name
    }
