import pytest
import uuid
from apps.base.factories import UserFactory
from apps.client_orders.factories import CountryFactory, CityFactory


@pytest.fixture
def user(db):
    return UserFactory.create(username="adel")

@pytest.fixture
def random_uuid():
    return str(uuid.uuid4())

@pytest.fixture
def country(db):
    return CountryFactory.create(name="Morocco")

@pytest.fixture
def city(db, country):
    return CityFactory.create(country=country, name="Tetouan")
