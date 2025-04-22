import pytest
from apps.supplier_orders.factories import SupplierFactory
from apps.base.factories import UserFactory
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
def supplier(db, user):
    return SupplierFactory.create(created_by=user)