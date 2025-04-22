import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from apps.client_orders.models import (
    Country,
    City,
    AcquisitionSource,
    Client,
    OrderStatus,
)
from apps.client_orders.factories import (
    CountryFactory,
    CityFactory,
    LocationFactory,
    AcquisitionSourceFactory,
    ClientFactory,
    OrderStatusFactory,
    ClientOrderFactory,
    ClientOrderedItemFactory
)


@pytest.mark.django_db
class TestCountryModel:
    """Tests for the Country Model"""

    def test_country_str_representation(self):
        country = CountryFactory.create(name="Morocco")
        assert str(country) == "Morocco"

    def test_country_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            Country.objects.create(name=None)

    def test_country_validation_fails_with_blank_name(self):
        country = Country(name="")
        with pytest.raises(ValidationError):
            country.full_clean()

    def test_country_creation_fails_with_existing_name(self):
        CountryFactory.create(name="Morocco")
        with pytest.raises(IntegrityError):
            CountryFactory.create(name="Morocco")

    def test_country_with_multiple_cities(self, country):
        cities = CityFactory.create_batch(4, country=country)
        assert all(city.country == country for city in cities)


@pytest.mark.django_db
class TestCityModel:
    """Tests for the City Model"""

    def test_city_creation_with_country(self, country):
        city = CityFactory.create(country=country)

        assert city.country is not None
        assert city.country == country
        assert city.country.name == "Morocco"

    def test_city_str_representation(self, country):
        city = CityFactory.create(country=country, name="Tetouan")
        assert str(city) == "Tetouan, Morocco"

    def test_city_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            City.objects.create(name=None)

    def test_city_creation_fails_without_country(self):
        with pytest.raises(IntegrityError):
            CityFactory.create(country=None)

    def test_city_validation_fails_with_blank_name(self, country):
        city = City(country=country, name="")
        with pytest.raises(ValidationError):
            city.full_clean()

    def test_city_creation_fails_with_existing_city_country_relationship(self, country):
        CityFactory.create(name="Tetouan", country=country)
        with pytest.raises(IntegrityError):
            CityFactory.create(name="Tetouan", country=country)


@pytest.mark.django_db
class TestLocationModel:
    """Tests for the Location Model"""

    def test_location_creation_with_related_objects(self, user, country, city):
        # Test with custom added_by, country, and city
        location = LocationFactory.create(added_by=user, country=country, city=city)
        assert location.added_by == user
        assert location.country == country
        assert location.city == city

    def test_location_str_representation(self, user, country, city):
        # Test full address with all fields
        location = LocationFactory.create(
            added_by=user, country=country, city=city, street_address="5th avenue"
        )
        assert str(location) == "5th avenue, Tetouan, Morocco added by: adel"

        # Test without added_by
        location = LocationFactory.create(
            added_by=None, country=country, city=city, street_address="5th avenue"
        )
        assert str(location) == "5th avenue, Tetouan, Morocco"

        # Test without country
        location = LocationFactory.create(
            added_by=user, country=None, city=city, street_address="5th avenue"
        )
        assert str(location) == "5th avenue, Tetouan added by: adel"

        # Test without city
        location = LocationFactory.create(
            added_by=user, country=country, city=None, street_address="5th avenue"
        )
        assert str(location) == "5th avenue, Morocco added by: adel"

        # Test without street address
        location = LocationFactory.create(
            added_by=user, country=country, city=city, street_address=None
        )
        assert str(location) == "Tetouan, Morocco added by: adel"
    
    def test_location_with_multiple_clients(self, location):
        clients = ClientFactory.create_batch(3, location=location)
        assert all(client.location == location for client in clients)
    
    def test_location_with_multiple_client_orders(self, location):
        orders = ClientOrderFactory.create_batch(3, shipping_address=location)
        assert all(order.shipping_address == location for order in orders)


@pytest.mark.django_db
class TestAcquisitionSourceModel:
    """Tests for the Acquisition Source Model"""

    def test_acq_source_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            AcquisitionSource.objects.create(name=None)
    
    def test_acq_source_validation_fails_with_blank_name(self):
        acq_source = AcquisitionSource(name="")
        with pytest.raises(ValidationError):
            acq_source.full_clean()
    
    def test_acq_source_creation_fails_with_existing_name(self):
        AcquisitionSourceFactory.create(name="ADS")
        with pytest.raises(IntegrityError):
            AcquisitionSourceFactory.create(name="ADS")

    def test_acq_source_creation_with_user(self, user):
        acq_source = AcquisitionSourceFactory.create(added_by=user)

        assert acq_source.added_by is not None
        assert acq_source.added_by == user
        assert acq_source.added_by.username == "adel"
    
    def test_acq_source_str_representation(self, user):
        # Test str representation without added_by attribute
        acq_source = AcquisitionSourceFactory.create(name="ADS", added_by=None)
        assert str(acq_source) == "ADS"

        # Test str representation with added_by attribute
        acq_source = AcquisitionSourceFactory.create(name="FB ADS", added_by=user)
        assert str(acq_source) == "FB ADS added by: adel"
    
    def test_acq_source_with_multiple_clients(self, source):
        clients = ClientFactory.create_batch(3, source=source)
        assert all(client.source == source for client in clients)

    def test_acq_source_with_multiple_client_orders(self, source):
        orders = ClientOrderFactory.create_batch(3, source=source)
        assert all(order.source == source for order in orders)


@pytest.mark.django_db
class TestClientModel:
    """Tests for the Client Model"""

    def test_client_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            Client.objects.create(name=None)

    def test_client_creation_fails_with_existing_name(self):
        ClientFactory.create(name="adel")
        with pytest.raises(IntegrityError):
            ClientFactory.create(name="adel")

    def test_client_validation_fails_with_blank_name(self):
        client = Client(name="")
        with pytest.raises(ValidationError):
            client.full_clean()

    def test_client_creation_with_related_objects(self, user, location, source):
        client = ClientFactory.create(
            created_by=user,
            location=location,
            source=source
        )

        assert client.created_by == user
        assert client.location == location
        assert client.source == source

    def test_client_str_representation(self):
        client = ClientFactory.create(name="Haitam")
        assert str(client) == "Haitam"

    def test_client_with_multiple_client_orders(self, client):
        orders = ClientOrderFactory.create_batch(3, client=client)
        assert all(order.client == client for order in orders)


@pytest.mark.django_db
class TestOrderStatusModel:
    """Tests for the Order Status Model"""

    def test_order_status_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            OrderStatus.objects.create(name=None)

    def test_order_status_validation_fails_with_blank_name(self):
        order_status = OrderStatus(name="")
        with pytest.raises(ValidationError):
            order_status.full_clean()

    def test_order_status_creation_fails_with_existing_name(self):
        OrderStatusFactory.create(name="Pending")
        with pytest.raises(IntegrityError):
            OrderStatusFactory.create(name="Pending")

    def test_order_status_str_representation(self):
        status = OrderStatusFactory.create(name="Pending")
        assert str(status) == "Pending"

    def test_order_status_with_multiple_client_orders(self, pending_status):
        orders = ClientOrderFactory.create_batch(
            3, delivery_status=pending_status, payment_status=pending_status
        )
        assert all(order.delivery_status == pending_status for order in orders)
        assert all(order.payment_status == pending_status for order in orders)


@pytest.mark.django_db
class TestClientOrderModel:
    """Tests for the Client Order Model"""

    def test_client_order_creation_with_related_objects(
        self,
        user,
        location,
        source,
        client,
        pending_status,
    ):
        client_order = ClientOrderFactory.create(
            created_by=user,
            client=client,
            shipping_address=location,
            source=source,
            delivery_status=pending_status,
            payment_status=pending_status,
        )

        assert client_order.created_by == user
        assert client_order.client == client
        assert client_order.shipping_address == location
        assert client_order.source == source
        assert client_order.delivery_status == pending_status
        assert client_order.payment_status == pending_status

    def test_client_order_str_representation(self):
        client_order = ClientOrderFactory.create()

        assert hasattr(client_order, 'reference_id')
        assert client_order.reference_id is not None
        assert str(client_order) == client_order.reference_id

    def test_client_order_with_multiple_ordered_items(self, client_order):
        ordered_items = ClientOrderedItemFactory.create_batch(
            4, order=client_order
        )
        assert all(item.order == client_order for item in ordered_items)


@pytest.mark.django_db
class TestClientOrderedItemModel:
    """Tests for the Client Ordered Item Model"""

    def test_client_ordered_item_creation_with_related_objects(
        self,
        user,
        client_order,
        item
    ):
        ordered_item = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order,
            item=item
        )

        assert ordered_item.created_by == user
        assert ordered_item.order == client_order
        assert ordered_item.item == item

    def test_client_ordered_item_str_representation(
        self,                                            
        user,
        client_order,
        item
    ):
        ordered_item = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order,
            item=item,
            ordered_quantity=4
        )

        assert str(ordered_item) == "Haitam ordered 4 of Projector"

    def test_ordered_item_creation_fails_without_related_item(self):
        with pytest.raises(IntegrityError):
            ClientOrderedItemFactory.create(item=None)

    def test_ordered_item_creation_fails_without_quantity(self):
        with pytest.raises(IntegrityError):
            ClientOrderedItemFactory.create(ordered_quantity=None)
    
    def test_ordered_item_creation_fails_without_price(self):
        with pytest.raises(IntegrityError):
            ClientOrderedItemFactory.create(ordered_price=None)

    def test_ordered_item_validation_fails_with_quantity_less_than_one(self):
        item = ClientOrderedItemFactory.create(ordered_quantity=-1)
        with pytest.raises(ValidationError):
            item.full_clean()
    
    def test_ordered_item_validation_fails_with_negative_price(self):
        item = ClientOrderedItemFactory.create(ordered_price=-1)
        with pytest.raises(ValidationError):
            item.full_clean()
