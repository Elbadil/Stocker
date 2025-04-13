import pytest
from unittest.mock import patch
from rest_framework.exceptions import ValidationError
from utils.serializers import (
    default_datetime_str_format,
    date_repr_format,
    get_location,
    decimal_to_float
)
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.inventory.models import Item
from apps.inventory.factories import ItemFactory
from apps.sales.models import Sale
from apps.client_orders.models import (
    Country,
    City,
    Location,
    AcquisitionSource
)
from apps.client_orders.serializers import (
    CountrySerializer,
    CitySerializer,
    LocationSerializer,
    AcquisitionSourceSerializer,
    OrderStatusSerializer,
    ClientSerializer,
    ClientOrderSerializer,
    ClientOrderedItemSerializer,
)
from apps.client_orders.factories import (
    CountryFactory,
    CityFactory,
    LocationFactory,
    AcquisitionSourceFactory,
    ClientFactory,
    OrderStatusFactory,
    ClientOrderedItemFactory
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


@pytest.mark.django_db
class TestCountrySerializer:
    """Tests for the Country Serializer"""

    def test_country_creation_with_valid_data(self):
        data = {"name": "Morocco"}
        serializer = CountrySerializer(data=data)
        assert serializer.is_valid()

        country = serializer.save()
        assert country.name == "Morocco"
    
    def test_country_creation_fails_without_name(self):
        serializer = CountrySerializer(data={})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]
    
    def test_country_creation_fails_with_existing_name(self):
        # Create a country with the name Morocco
        CountryFactory.create(name="Morocco")

        # Create another country with the same name
        serializer = CountrySerializer(data={"name": "Morocco"})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert (
            serializer.errors["name"] ==
            ["country with this name already exists."]
        )

    def test_country_serializer_data_fields(self, country):
        serializer = CountrySerializer(country)

        assert "id" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_country_serializer_data_fields_types(self, country):
        serializer = CountrySerializer(country)
        country_data = serializer.data

        assert type(country_data["id"]) == str
        assert type(country_data["name"]) == str
        assert type(country_data["created_at"]) == str
        assert type(country_data["updated_at"]) == str

    def test_country_serializer_data(self, country):
        serializer = CountrySerializer(country)
        country_data = serializer.data
    
        assert country_data["id"] == country.id
        assert country_data["name"] == "Morocco"
        assert (
            country_data["created_at"] ==
            default_datetime_str_format(country.created_at)
        )
        assert (
            country_data["updated_at"] ==
            default_datetime_str_format(country.updated_at)
        )

    def test_country_update(self, country):
        country_name = country.name

        serializer = CountrySerializer(country, data={"name": "Algeria"})
        assert serializer.is_valid()

        country_update = serializer.save()
        assert country_update.name == "Algeria"
        assert country_update.name != country_name


@pytest.mark.django_db
class TestCitySerializer:
    """Tests for the City Serializer"""

    def test_city_creation_with_valid_data(self, country):
        data = {
            "country": country.id,
            "name": "Tetouan"
        }
        serializer = CitySerializer(data=data)
        assert serializer.is_valid()

        city = serializer.save()
        assert city.name == "Tetouan"
        assert city.country is not None
        assert str(city.country.id) == str(country.id)

    def test_city_creation_fails_without_name(self, country):
        serializer = CitySerializer(data={"country": country.id})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]

    def test_city_creation_fails_without_country(self):
        serializer = CitySerializer(data={"name": "Tetouan"})

        assert not serializer.is_valid()
        assert "country" in serializer.errors
        assert serializer.errors["country"] == ["This field is required."]
    
    def test_city_creation_fails_with_existing_city_country_relationship(
        self,
        country
    ):
        # Create a city with the name Tetouan and Morocco country instance
        CityFactory.create(name="Tetouan", country=country)

        # Create a city with the same name and country instance
        serializer = CitySerializer(
            data={
                "country": country.id,
                "name": "Tetouan"
            }
        )
        assert not serializer.is_valid()

        assert "non_field_errors" in serializer.errors
        assert (
            serializer.errors["non_field_errors"] ==
            ["The fields name, country must make a unique set."]
        )

    def test_city_serializer_data_fields(self, city):
        serializer = CitySerializer(city)

        assert "id" in serializer.data
        assert "name" in serializer.data
        assert "country" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_city_serializer_data_fields_types(self, city):
        serializer = CitySerializer(city)
        city_data = serializer.data

        assert type(city_data["id"]) == str
        assert type(city_data["name"]) == str
        assert type(city_data["country"]) == str
        assert type(city_data["created_at"]) == str
        assert type(city_data["updated_at"]) == str

    def test_city_serializer_data(self, city):
        serializer = CitySerializer(city)
        city_data = serializer.data

        assert city_data["id"] == city.id
        assert city_data["name"] == "Tetouan"
        assert city_data["country"] == city.country.id
        assert (
            city_data["created_at"] ==
            default_datetime_str_format(city.created_at)
        )
        assert (
            city_data["updated_at"] ==
            default_datetime_str_format(city.updated_at)
        )

    def test_city_update(self, city, country):
        city_name = city.name

        serializer = CitySerializer(
            city,
            data={
                "country": country.id,
                "name": "Tangier"
            }
        )
        assert serializer.is_valid()

        city_update = serializer.save()
        assert city_update.name == "Tangier"
        assert city_update.name != city_name

    def test_city_update(self, city):
        city_name = city.name

        serializer = CitySerializer(
            city,
            data={"name": "Tangier"},
            partial=True
        )
        assert serializer.is_valid()

        city_update = serializer.save()
        assert city_update.name == "Tangier"
        assert city_update.name != city_name


@pytest.mark.django_db
class TestLocationSerializer:
    """Tests for the Location Serializer"""

    def test_location_serializer_retrieves_country_and_city_by_name(
        self,
        country,
        city
    ):
        location_data = {
            "country": country.name,
            "city": city.name,
        }
        serializer = LocationSerializer(data=location_data)
        assert serializer.is_valid()

        location = serializer.save()
        assert location.country is not None
        assert isinstance(location.country, Country)
        assert str(location.country.id) == str(country.id)

        assert location.city is not None
        assert isinstance(location.city, City)
        assert str(location.city.id) == str(city.id)

    def test_location_serializer_sets_added_by_from_context(
        self,
        user,
        location_data
    ):
        serializer = LocationSerializer(
            data=location_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        location = serializer.save()
        assert location.added_by is not None
        assert str(location.added_by.id) == str(user.id)

    def test_location_creation_with_valid_data(self, country, city, user):
        location_data = {
            "country": country.name,
            "city": city.name,
            "street_address": "5th avenue"
        }

        serializer = LocationSerializer(
            data=location_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        location = serializer.save()
        assert str(location.added_by.id) == str(user.id)
        assert str(location.country.id) == str(country.id)
        assert str(location.city.id) == str(city.id)
        assert location.street_address == location_data["street_address"]

    def test_location_creation_fails_without_country(self, location_data):
        location_data.pop("country")

        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "country" in serializer.errors
        assert serializer.errors["country"] == ["This field is required."]
    
    def test_location_creation_fails_with_country_set_to_none(
        self,
        location_data
    ):
        location_data["country"] = None
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "country" in serializer.errors
        assert (
            serializer.errors["country"] ==
            ["Country is required to add a location."]
        )

    def test_location_creation_fails_with_blank_country(
        self,
        location_data
    ):
        location_data["country"] = ""
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "country" in serializer.errors
        assert (
            serializer.errors["country"] ==
            ["Country is required to add a location."]
        )
    
    def test_location_creation_fails_with_inexistent_country(self, location_data):
        location_data["country"] = "Bard"
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "country" in serializer.errors
        assert (
            serializer.errors["country"] ==
            ["Invalid country."]
        )

    def test_location_creation_fails_without_city(self, location_data):
        location_data.pop("city")

        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "city" in serializer.errors
        assert serializer.errors["city"] == ["This field is required."]

    def test_location_creation_fails_with_city_set_to_none(
        self,
        location_data
    ):
        location_data["city"] = None
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "city" in serializer.errors
        assert (
            serializer.errors["city"] ==
            ["City is required to add a location."]
        )

    def test_location_creation_fails_with_blank_city(
        self,
        location_data
    ):
        location_data["city"] = ""
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "city" in serializer.errors
        assert (
            serializer.errors["city"] ==
            ["City is required to add a location."]
        )

    def test_location_creation_fails_with_inexistent_city(self, location_data):
        location_data["city"] = "Bard"
        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "city" in serializer.errors
        assert (
            serializer.errors["city"] ==
            ["Invalid city."]
        )

    def test_location_creation_fails_with_non_linked_city_and_country(
        self,
        location_data
    ):
        country = CountryFactory.create(name="Algeria")
        location_data["country"] = country.name

        serializer = LocationSerializer(data=location_data)
        assert not serializer.is_valid()

        assert "city" in serializer.errors
        assert (
            serializer.errors["city"] ==
            ["City does not belong to the country provided."]
        )

    def test_location_street_address_field_is_optional(self, location_data):
        location_data.pop('street_address')

        serializer = LocationSerializer(data=location_data)
        assert serializer.is_valid()

        location = serializer.save()
        assert location.street_address is None

    def test_location_added_by_field_is_optional(self, location_data):
        # Create a location without passing a user
        # in the serializer's context
        serializer = LocationSerializer(data=location_data)
        assert serializer.is_valid()

        location = serializer.save()
        assert location.added_by is None

    def test_location_create_retrieves_location_if_attributes_are_the_same(
        self,
        country,
        city,
        location_data
    ):
        # Create a location
        location_1 = LocationFactory.create(
            added_by=None,
            country=country,
            city=city,
            street_address="5th avenue"
        )

        initial_location_count = Location.objects.count()

        # Verify location_data has the same attributes as the existing location 
        assert location_1.country.name == location_data["country"]
        assert location_1.city.name == location_data["city"]
        assert location_1.street_address == location_data["street_address"]

        # Create another location with the same attributes
        serializer = LocationSerializer(data=location_data)
        assert serializer.is_valid()

        location_2 = serializer.save()

        # Verify no additional location has been created
        assert str(location_1.id) == str(location_2.id)
        assert Location.objects.count() == initial_location_count

    def test_location_serializer_data_fields(self, location):
        serializer = LocationSerializer(location)

        assert "id" in serializer.data
        assert "added_by" in serializer.data
        assert "country" in serializer.data
        assert "city" in serializer.data
        assert "street_address" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_location_serializer_data_fields_types(self, location):
        serializer = LocationSerializer(location)
        location_data = serializer.data

        assert type(location_data["id"]) == str
        assert type(location_data["added_by"]) == str
        assert type(location_data["country"]) == str
        assert type(location_data["city"]) == str
        assert type(location_data["street_address"]) == str
        assert type(location_data["created_at"]) == str
        assert type(location_data["created_at"]) == str

    def test_location_serializer_data(self, location):
        serializer = LocationSerializer(location)
        location_data = serializer.data

        assert location_data["id"] == location.id
        assert location_data["added_by"] == location.added_by.username
        assert location_data["country"] == location.country.name
        assert location_data["city"] == location.city.name
        assert location_data["street_address"] == location.street_address
        assert (
            location_data["created_at"] ==
            default_datetime_str_format(location.created_at)
        )
        assert (
            location_data["updated_at"] ==
            default_datetime_str_format(location.updated_at)
        )


@pytest.mark.django_db
class TestAcquisitionSourceSerializer:
    """Tests for the Acquisition Source Serializer"""

    def test_acq_source_creation_with_valid_data(self, user):
        data = {
            "added_by": user.id,
            "name": "ADS"
        }
        serializer = AcquisitionSourceSerializer(data=data)
        assert serializer.is_valid()

        source = serializer.save()
        assert source.name == "ADS"
        assert str(source.added_by.id) == str(user.id)

    def test_acq_source_creation_fails_without_name(self):
        serializer = AcquisitionSourceSerializer(data={})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]

    def test_acq_source_creation_fails_with_existing_name(self):
        # Create a source with the name ADS
        AcquisitionSourceFactory.create(name="ADS")

        # Create another source with the same name
        serializer = AcquisitionSourceSerializer(data={"name": "ADS"})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert (
            serializer.errors["name"] ==
            ["acquisition source with this name already exists."]
        )

    def test_acq_source_creation_added_by_field_is_optional(self):
        serializer = AcquisitionSourceSerializer(data={"name": "ADS"})
        assert serializer.is_valid()

        source = serializer.save()
        assert source.added_by is None

    def test_acq_source_serializer_data_fields(self, source):
        serializer = AcquisitionSourceSerializer(source)

        assert "id" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_acq_source_serializer_data_fields_types(self, source):
        serializer = AcquisitionSourceSerializer(source)
        source_data = serializer.data

        assert type(source_data["id"]) == str
        assert type(source_data["name"]) == str
        assert type(source_data["created_at"]) == str
        assert type(source_data["updated_at"]) == str

    def test_acq_source_serializer_data(self, source):
        serializer = AcquisitionSourceSerializer(source)
        source_data = serializer.data

        assert source_data["id"] == source.id
        assert source_data["name"] == "ADS"
        assert (
            source_data["created_at"] ==
            default_datetime_str_format(source.created_at)
        )
        assert (
            source_data["updated_at"] ==
            default_datetime_str_format(source.updated_at)
        )

    def test_acq_source_update(self, source):
        source_name = source.name

        serializer = AcquisitionSourceSerializer(
            source,
            data={"name": "Direct"}
        )
        assert serializer.is_valid()

        source_update = serializer.save()
        assert source_update.name == "Direct"
        assert source_update.name != source_name


@pytest.mark.django_db
class TestOrderStatusSerializer:
    """Tests for the Order Status Serializer"""

    def test_order_status_creation_with_valid_data(self):
        data = {"name": "Pending"}
        serializer = OrderStatusSerializer(data=data)
        assert serializer.is_valid()

        status = serializer.save()
        assert status.name == "Pending"
    
    def test_order_status_creation_fails_without_name(self):
        serializer = OrderStatusSerializer(data={})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]
    
    def test_order_status_creation_fails_with_existing_name(self):
        # Create a order with the name Pending
        OrderStatusFactory.create(name="Pending")

        # Create another order_status with the same name
        serializer = OrderStatusSerializer(data={"name": "Pending"})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert (
            serializer.errors["name"] ==
            ["order status with this name already exists."]
        )

    def test_order_status_serializer_data_fields(self, pending_status):
        serializer = OrderStatusSerializer(pending_status)

        assert "id" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_order_status_serializer_data_fields_types(self, pending_status):
        serializer = OrderStatusSerializer(pending_status)
        pending_status_data = serializer.data

        assert type(pending_status_data["id"]) == str
        assert type(pending_status_data["name"]) == str
        assert type(pending_status_data["created_at"]) == str
        assert type(pending_status_data["updated_at"]) == str

    def test_order_status_serializer_data(self, pending_status):
        serializer = OrderStatusSerializer(pending_status)
        pending_status_data = serializer.data
    
        assert pending_status_data["id"] == pending_status.id
        assert pending_status_data["name"] == "Pending"
        assert (
            pending_status_data["created_at"] ==
            default_datetime_str_format(pending_status.created_at)
        )
        assert (
            pending_status_data["updated_at"] ==
            default_datetime_str_format(pending_status.updated_at)
        )

    def test_order_status_update(self, pending_status):
        pending_status_name = pending_status.name

        serializer = OrderStatusSerializer(pending_status, data={"name": "Failed"})
        assert serializer.is_valid()

        order_status_update = serializer.save()
        assert order_status_update.name == "Failed"
        assert order_status_update.name != pending_status_name


@pytest.mark.django_db
class TestClientSerializer:
    """Tests for the Client Serializer"""

    def test_client_serializer_sets_created_by_from_context(
        self,
        user,
    ):
        serializer = ClientSerializer(
            data={"name": "Haitam"},
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.created_by is not None
        assert str(client.created_by.id) == str(user.id)

    def test_client_creation_with_valid_data(self, user):
        client_data = {
            "name": "Haitam",
            "age": 23,
            "phone_number": "0628273523",
            "email": "haitam@gmail.com",
            "sex": "Male"
        }
        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert str(client.created_by.id) == str(user.id)
        assert client.name == client_data["name"]
        assert client.age == client_data["age"]
        assert client.phone_number == client_data["phone_number"]
        assert client.email == client_data["email"]
        assert client.sex == client_data["sex"]

    def test_client_creation_fails_without_name(self, user):
        serializer = ClientSerializer(data={}, context={'user': user})
        assert not serializer.is_valid()

        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]

    def test_client_creation_fails_with_existing_name(self, user):
        # Create a client with the name Haitam
        ClientFactory.create(name="Haitam")

        # Create another client using ClientSerializer with the same name
        serializer = ClientSerializer(
            data={"name": "Haitam"},
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "name" in serializer.errors
        assert (
            serializer.errors["name"] ==
            ["client with this name already exists."]
        )
    
    def test_client_creation_with_invalid_email(self, user):
        client_data = {
            "name": "Haitam",
            "email": "haitamgmail.com"
        }
        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "email" in serializer.errors
        assert serializer.errors["email"] == ["Enter a valid email address."]
    
    def test_client_creation_creates_new_location_if_not_exists(
        self,
        user,
        location_data
    ):
        # Verify location does not exist before client creation
        assert not Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).exists()

        # Define client data with the inexistent location data
        client_data = {
            "name": "Haitam",
            "location": location_data
        }

        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.location is not None

        # Verify location has been created and set to client after client creation
        location =  Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).first()
        assert location is not None
        assert str(client.location.id) == str(location.id)

    def test_client_creation_retrieves_existing_location(
        self,
        user,
        location
    ):
        initial_location_count = Location.objects.count()

        # Set for client's location the same existing location's data
        client_data = {
            "name": "Haitam",
            "location": {
                "country": location.country.name,
                "city": location.city.name,
                "street_address": location.street_address
            }
        }

        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.location is not None

        # Verify the client's location was set to the exact 
        # existing location
        assert str(client.location.id) == str(location.id)

        # Verify no new location was created
        assert Location.objects.count() == initial_location_count

    def test_client_creation_uses_location_serializer(self, user, location_data):
        client_data = {
            "name": "Haitam",
            "location": location_data
        }

        # Mock the location serializer to verify it's called
        location_serializer_path = "apps.client_orders.serializers.LocationSerializer"
        with patch(location_serializer_path) as mock_location_serializer:
            # Mock instance of the location serializer
            mock_location_instance = mock_location_serializer.return_value
            mock_location_instance.is_valid.return_value = True
            mock_location_instance.save.return_value = LocationFactory.create()

            # Call the client serializer
            serializer = ClientSerializer(data=client_data, context={'user': user})
            assert serializer.is_valid()

            client = serializer.save()

            assert client.name == "Haitam"

            # Verify location serializer was called with the correct data
            mock_location_serializer.assert_called_once_with(
                data=location_data,
                context={'user': user}
            )

            # Verify save was called on the location serializer
            mock_location_instance.save.assert_called_once()

            # Verify the created location was linked to the client
            assert client.location == mock_location_instance.save.return_value

    def test_client_creation_creates_new_source_if_not_exists(
        self,
        user,
    ):
        # Verify acq source does not exist before client creation
        assert not AcquisitionSource.objects.filter(name__iexact="ADS").exists()

        # Define client data with the inexistent source name
        client_data = {
            "name": "Haitam",
            "source": "ADS"
        }

        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.source is not None

        # Verify acq source has been created after client creation
        source = AcquisitionSource.objects.filter(name__iexact="ADS").first()
        assert source is not None
        assert str(client.source.id) == str(source.id)

    def test_client_creation_retrieves_existing_source_by_name(
        self,
        user,
        source
    ):
        initial_acq_source_count = AcquisitionSource.objects.count()

        client_data = {
            "name": "Haitam",
            "source": "ADS"
        }

        serializer = ClientSerializer(
            data=client_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.source is not None
        assert str(client.source.id) == str(source.id)

        # Verify no new acq source was created
        assert AcquisitionSource.objects.count() == initial_acq_source_count

    def test_client_creation_registers_new_activity(self, user):
        serializer = ClientSerializer(
            data={"name": "Haitam"},
            context={'user': user}
        )
        assert serializer.is_valid()

        client = serializer.save()
        assert client.name == "Haitam"
        
        assert Activity.objects.filter(
            action="created",
            model_name="client",
            object_ref__contains="Haitam"
        ).exists()

    def test_client_update(self, user, client):
        client_name = client.name

        serializer = ClientSerializer(
            client,
            data={"name": "Safuan"},
            context={'user': user}
        )
        assert serializer.is_valid()

        client_update = serializer.save()
        assert client_update.name != client_name

    def test_client_partial_update(self, user, location, source):
        client = ClientFactory.create(
            name="Haitam",
            created_by=user,
            location=location,
            source=source
        )
        client_name = client.name

        serializer = ClientSerializer(
            client,
            data={"name": "Safuan"},
            context={'user': user}
        )
        assert serializer.is_valid()

        client_update = serializer.save()
        assert client_update.name != client_name

    def test_client_update_removes_optional_field_if_set_to_none(
        self,
        user,
        location,
        source
    ):
        client = ClientFactory.create(
            created_by=user,
            location=location,
            source=source
        )
        assert client.location is not None
        assert client.source is not None

        serializer = ClientSerializer(
            client,
            data={
                "location": None,
                "source": None,
            },
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        client_update = serializer.save()
        assert client_update.updated
        assert client.location is None
        assert client.source is None

    def test_client_update_registers_new_activity(self, user, client):
        client_age = client.age

        serializer = ClientSerializer(
            client,
            data={"age": client_age + 2},
            context={'user': user},
            partial=True
        )
        assert serializer.is_valid()

        client_update = serializer.save()
        assert client_update.age != client_age
        assert client_update.name == "Haitam"

        assert Activity.objects.filter(
            action="updated",
            model_name="client",
            object_ref__contains="Haitam"
        ).exists()

    def test_client_serializer_data_fields(self, client):
        serializer = ClientSerializer(client)

        expected_fields = {
            "id",
            "created_by",
            "name",
            "age",
            "phone_number",
            "email",
            "sex",
            "location",
            "source",
            "total_orders",
            "updated",
            "created_at",
            "updated_at"
        }

        assert expected_fields.issubset(serializer.data.keys())

    def test_client_serializer_data_fields_types(self, client):
        serializer = ClientSerializer(client)
        client_data = serializer.data

        assert type(client_data["id"]) == str
        assert type(client_data["created_by"]) == str
        assert type(client_data["name"]) == str
        assert type(client_data["age"]) == int
        assert type(client_data["phone_number"]) == str
        assert type(client_data["email"]) == str
        assert type(client_data["sex"]) == str
        assert type(client_data["location"]) == dict
        assert type(client_data["source"]) == str
        assert type(client_data["total_orders"]) == int
        assert type(client_data["updated"]) == bool
        assert type(client_data["created_at"]) == str
        assert type(client_data["updated_at"]) == str

    def test_client_serializer_data(self, client):
        serializer = ClientSerializer(client)
        client_data = serializer.data
    
        assert client_data["id"] == client.id
        assert client_data["created_by"] == client.created_by.username
        assert client_data["name"] == client.name
        assert client_data["age"] == client.age
        assert client_data["phone_number"] == client.phone_number
        assert client_data["email"] == client.email
        assert client_data["sex"] == client.sex
        assert client_data["location"] == get_location(client.location)
        assert client_data["source"] == client.source.name
        assert client_data["total_orders"] == client.total_orders
        assert client_data["updated"] == client.updated
        assert (
            client_data["created_at"] ==
            date_repr_format(client.created_at)
        )
        assert (
            client_data["updated_at"] ==
            date_repr_format(client.updated_at)
        )


@pytest.mark.django_db
class TestClientOrderItemSerializer:
    """Tests for the Client Ordered Item Serializer"""

    def test_ordered_item_serializer_sets_created_by_from_context(
        self,
        user,
        ordered_item_data
    ):
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        item = serializer.save()
        assert item.created_by is not None
        assert str(item.created_by.id) == str(user.id)

    def test_ordered_item_creation_with_valid_data(
        self,
        user,
        ordered_item_data
    ):
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        item = serializer.save()
        assert str(item.created_by.id) == str(user.id)
        assert str(item.order.id) == str(ordered_item_data["order"])
        assert item.ordered_quantity == ordered_item_data["ordered_quantity"]
        assert item.ordered_price == ordered_item_data["ordered_price"]

    def test_ordered_item_creation_fails_without_order(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop("order")
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "order" in serializer.errors
        assert serializer.errors["order"] == ["This field is required."]

    def test_ordered_item_creation_fails_without_related_item(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop("item")
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert serializer.errors["item"] == ["This field is required."]

    def test_ordered_item_creation_fails_without_quantity(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop("ordered_quantity")
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "ordered_quantity" in serializer.errors
        assert serializer.errors["ordered_quantity"] == ["This field is required."]

    def test_ordered_item_creation_fails_without_price(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop("ordered_price")
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "ordered_price" in serializer.errors
        assert serializer.errors["ordered_price"] == ["This field is required."]

    def test_ordered_item_creation_fails_with_quantity_less_than_one(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data["ordered_quantity"] = 0
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "ordered_quantity" in serializer.errors
        assert (
            serializer.errors["ordered_quantity"] ==
            ["Ensure this value is greater than or equal to 1."]
        )

    def test_ordered_item_creation_fails_with_negative_price(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data["ordered_price"] = -1
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "ordered_price" in serializer.errors
        assert (
            serializer.errors["ordered_price"] ==
            ["Ensure this value is greater than or equal to 0.0."]
        )

    def test_ordered_item_serializer_retrieves_related_item_by_name(
        self,
        user,
        ordered_item_data
    ):
        related_item = ordered_item_data["item"]
        assert related_item == "Projector"

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors
        
        ordered_item = serializer.save()
        assert ordered_item.item is not None
        assert isinstance(ordered_item.item, Item)
        assert ordered_item.item.name == related_item

    def test_ordered_item_creation_fails_with_inexistent_item(
        self,
        user,
        ordered_item_data
    ):
        random_name = "RandomItemName"
        ordered_item_data["item"] = random_name
        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{random_name}' does not exist in your inventory."]
        )

    def test_ordered_item_creation_fails_with_item_not_in_inventory(
        self,
        user,
        ordered_item_data
    ):
        item = ItemFactory.create(in_inventory=False)
        ordered_item_data["item"] = item.name

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{item.name}' does not exist in your inventory."]
        )

    def test_ordered_item_creation_fails_for_non_owned_item(
        self,
        user,
        ordered_item_data
    ):
        user_2 = UserFactory.create()
        item = ItemFactory.create(created_by=user_2)
        ordered_item_data["item"] = item.name

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{item.name}' does not exist in your inventory."]
        )

    def test_ordered_item_creation_fails_for_delivered_orders(
        self,
        user,
        client_order,
        delivered_status,
        ordered_item_data
    ):
        # Update order delivery status to delivered
        client_order.delivery_status = delivered_status
        client_order.save()

        ordered_item_data["order"] = client_order.id

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "order" in errors.value.detail
        assert errors.value.detail["order"] == (
            "Cannot apply changes to the order "
            f"with ID '{client_order.id}' ordered items "
            "because it has already been marked as Delivered. "
            "Changes to delivered orders are restricted "
            "to maintain data integrity."
        )

    def test_ordered_item_creation_fails_with_existing_item_in_order(
        self,
        user,
        item,
        client_order,
        ordered_item_data
    ):
        # Create ordered item with the same item and order that will
        # be used to create an ordered item with ClientOrderedItemSerializer
        ordered_item = ClientOrderedItemFactory.create(
            item=item,
            order=client_order
        )

        # Ensure that the created ordered item has the same name and order id
        # of the ordered_item_data's item and order
        assert ordered_item.item.name == ordered_item_data["item"]
        assert str(ordered_item.order.id) == str(ordered_item_data["order"])

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "item" in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{ordered_item.item.name}' already exists in the order's "
            "list of ordered items. Consider updating the existing item "
            "if you need to modify its details."
        )

    def test_ordered_quantity_exceeds_item_quantity_in_inventory(
        self,
        user,
        item,
        ordered_item_data
    ):
        ordered_quantity = 10
        ordered_item_data["ordered_quantity"] = ordered_quantity
        ordered_item_data["item"] = item.name

        assert ordered_quantity > item.quantity

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()
        
        assert "ordered_quantity" in errors.value.detail
        assert errors.value.detail["ordered_quantity"] == (
            f"The ordered quantity for '{item.name}' "
             "exceeds available stock."
        )

    def test_item_quantity_gets_reduced_by_ordered_quantity(
        self,
        user,
        item,
        ordered_item_data
    ):
        ordered_quantity = 3
        item_initial_quantity = item.quantity

        ordered_item_data["ordered_quantity"] = ordered_quantity
        ordered_item_data["item"] = item.name

        serializer = ClientOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()
        ordered_item = serializer.save()

        # Refresh the item from DB to reflect changes
        item.refresh_from_db()

        # Ensure ordered quantity was set correctly
        assert ordered_item.ordered_quantity == ordered_quantity

        # Ensure item quantity decreases by the correct amount
        assert item.quantity < item_initial_quantity
        assert item.quantity == item_initial_quantity - ordered_quantity

    def test_ordered_item_serializer_data_fields(self, ordered_item):
        serializer = ClientOrderedItemSerializer(ordered_item)

        expected_fields = {
            "id",
            "created_by",
            "order",
            "item",
            "ordered_quantity",
            "ordered_price",
            "total_price",
            "total_profit",
            "unit_profit",
            "created_at",
            "updated_at"
        }

        assert expected_fields.issubset(serializer.data.keys())

    def test_ordered_item_serializer_data_fields_types(self, ordered_item):
        serializer = ClientOrderedItemSerializer(ordered_item)
        ordered_item_data = serializer.data

        assert type(ordered_item_data["id"]) == str
        assert type(ordered_item_data["created_by"]) == str
        assert type(ordered_item_data["order"]) == str
        assert type(ordered_item_data["item"]) == str
        assert type(ordered_item_data["ordered_quantity"]) == int
        assert type(ordered_item_data["ordered_price"]) == float
        assert type(ordered_item_data["total_price"]) == float
        assert type(ordered_item_data["total_profit"]) == float
        assert type(ordered_item_data["unit_profit"]) == float
        assert type(ordered_item_data["created_at"]) == str
        assert type(ordered_item_data["updated_at"]) == str

    def test_ordered_item_serializer_data(self, ordered_item):
        serializer = ClientOrderedItemSerializer(ordered_item)
        item_data = serializer.data
    
        assert item_data["id"] == ordered_item.id
        assert item_data["created_by"] == ordered_item.created_by.username
        assert str(item_data["order"]) == str(ordered_item.order.id)
        assert item_data["item"] == ordered_item.item.name
        assert item_data["ordered_quantity"] == ordered_item.ordered_quantity

        # Decimal fields
        assert (
            item_data["ordered_price"] ==
            decimal_to_float(ordered_item.ordered_price)
        )
        assert (
            item_data["total_price"] ==
            decimal_to_float(ordered_item.total_price)
        )
        assert (
            item_data["total_profit"] ==
            decimal_to_float(ordered_item.total_profit)
        )
        assert (
            item_data["unit_profit"] ==
            decimal_to_float(ordered_item.unit_profit)
        )

        # Datetime fields
        assert (
            item_data["created_at"] ==
            date_repr_format(ordered_item.created_at)
        )
        assert (
            item_data["updated_at"] ==
            date_repr_format(ordered_item.updated_at)
        )
    
    def test_ordered_item_update(self, user, ordered_item, ordered_item_data):
        initial_ordered_quantity = ordered_item.ordered_quantity
        initial_ordered_price = ordered_item.ordered_price

        ordered_item_data["ordered_price"] = initial_ordered_price + 100
        ordered_item_data["ordered_price"] = initial_ordered_quantity - 1

        serializer = ClientOrderedItemSerializer(
            ordered_item,
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        item_update = serializer.save()
        assert item_update.ordered_quantity == ordered_item_data["ordered_quantity"]
        assert item_update.ordered_quantity != initial_ordered_quantity

        assert item_update.ordered_price == ordered_item_data["ordered_price"]
        assert item_update.ordered_price != initial_ordered_price

    def test_ordered_item_partial_update(
        self,
        user,
        ordered_item,
    ):
        initial_ordered_price = ordered_item.ordered_price

        serializer = ClientOrderedItemSerializer(
            ordered_item,
            data={
                "ordered_price": initial_ordered_price + 100
            },
            context={'user': user},
            partial=True
        )
        assert serializer.is_valid()

        item_update = serializer.save()

        assert item_update.ordered_price == initial_ordered_price + 100
        assert item_update.ordered_price != initial_ordered_price

    def test_ordered_item_update_fails_for_delivered_orders(
        self,
        user,
        client_order,
        ordered_item,
        ordered_item_data,
        delivered_status
    ):
        # Update order delivery status to delivered
        client_order.delivery_status = delivered_status
        client_order.save()

        assert str(client_order.id) == str(ordered_item_data["order"])

        serializer = ClientOrderedItemSerializer(
            ordered_item,
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "order" in errors.value.detail
        assert errors.value.detail["order"] == (
            "Cannot apply changes to the order "
            f"with ID '{client_order.id}' ordered items "
            "because it has already been marked as Delivered. "
            "Changes to delivered orders are restricted "
            "to maintain data integrity."
        )

    def test_ordered_item_update_validates_item_uniqueness_if_changed(
        self,
        user,
        ordered_item,
        client_order,
    ):
        # Create an item and add it to the order's ordered items
        item_pack = ItemFactory.create(
            created_by=user,
            name="Pack",
            in_inventory=True
        )
        ordered_item_pack = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order,
            item=item_pack
        )

        # Ensure both items belong to the same order
        assert str(ordered_item.order.id) == str(ordered_item_pack.order.id)

        # Attempt to update the ordered item's item
        serializer = ClientOrderedItemSerializer(
            ordered_item,
            data={"item": item_pack.name},
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        # Ensure validation error is raised for existing item in order's items list
        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "item" in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{item_pack.name}' already exists in the order's "
            "list of ordered items. Consider updating the existing item "
            "if you need to modify its details."
        )

    def test_ordered_item_update_recalculates_item_quantity(
        self,
        user,
        item,
        ordered_item
    ):
        assert str(item.id) == str(ordered_item.item.id)

        item_quantity = item.quantity
        ordered_quantity = ordered_item.ordered_quantity
        new_ordered_quantity = ordered_quantity - 2

        serializer = ClientOrderedItemSerializer(
            ordered_item,
            data={"ordered_quantity": new_ordered_quantity},
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        ordered_item_update = serializer.save()
        assert ordered_item_update.ordered_quantity == new_ordered_quantity

        # Ensure item in inventory gets back the ordered quantity difference
        item.refresh_from_db()
        assert item.quantity > item_quantity
        assert item.quantity == (
            item_quantity + (ordered_quantity - new_ordered_quantity)
        )


@pytest.mark.django_db
class TestClientOrderSerializer:
    """Tests for the Client Order Serializer"""

    def test_order_serializer_sets_created_by_from_context(
        self,
        user,
        order_data
    ):
        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.created_by is not None
        assert str(order.created_by.id) == str(user.id)

    def test_order_creation_with_valid_data(
        self,
        user,
        client,
        location,
        source,
        pending_status,
        order_data
    ):
        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert str(order.created_by.id) == str(user.id)
        assert str(order.client.id) == str(client.id)
        assert str(order.shipping_address.id) == str(location.id)
        assert str(order.delivery_status.id) == str(pending_status.id)
        assert str(order.payment_status.id) == str(pending_status.id)
        assert str(order.source.id) == str(source.id)

    def test_order_serializer_retrieves_client_by_name(self, user, client, order_data):
        assert client.name == order_data["client"]

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.client is not None
        assert order.client.name == order_data["client"]

    def test_order_creation_fails_without_client(self, user, order_data):
        order_data.pop("client")

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "client" in serializer.errors
        assert serializer.errors["client"] == ["This field is required."]

    def test_order_creation_fails_with_inexistent_client(self, user, order_data):
        random_client_name = "RandomClient"
        order_data["client"] = random_client_name

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        
        assert "client" in serializer.errors
        assert serializer.errors["client"] == [
            f"Client '{random_client_name}' does not exist. "
             "Please create a new client if this is a new entry."
        ]

    def test_order_creation_fails_with_non_owned_client(self, user, order_data):
        user_2 = UserFactory.create()
        user_2_client = ClientFactory.create(created_by=user_2)

        order_data["client"] = user_2_client.name

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "client" in serializer.errors
        assert serializer.errors["client"] == [
            f"Client '{user_2_client.name}' does not exist. "
             "Please create a new client if this is a new entry."
        ]

    def test_order_creation_fails_without_ordered_items(self, user, order_data):
        order_data.pop("ordered_items")

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert serializer.errors["ordered_items"] == ["This field is required."]

    def test_order_creation_fails_with_empty_ordered_items_list(self, user, order_data):
        order_data["ordered_items"] = []

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert serializer.errors["ordered_items"] == ["This field is required."]

    def test_order_creation_fails_with_empty_ordered_item_object(
        self,
        user,
        order_data
    ):
        # Append empty object to the ordered_items list
        order_data["ordered_items"].append({})

        assert len(order_data["ordered_items"]) == 2

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert serializer.errors["ordered_items"] == [
            f"Item at position 2 cannot be empty. Please provide valid details."
        ]

    def test_order_creation_fails_with_duplicate_ordered_item_object(
        self,
        user,
        order_data
    ):
        ordered_item_1 = order_data["ordered_items"][0]

        # Add ordered item with the same item name to the ordered_items list
        ordered_item_2 = {
            "item": ordered_item_1["item"],
            "quantity": 2,
            "price": 600
        }
        order_data["ordered_items"].append(ordered_item_2)

        assert len(order_data["ordered_items"]) == 2

        serializer = ClientOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert serializer.errors["ordered_items"] == [
            f"Item '{ordered_item_1['item']}' has been selected multiple times."
        ]

    def test_order_creation_uses_client_ordered_item_serializer(
        self,
        user,
        client,
        ordered_item_data,
    ):
        # Add second ordered item data object 
        item = ItemFactory.create(created_by=user, quantity=6, in_inventory=True)
        ordered_item_2_data = {
            "item": item.name,
            "quantity": item.quantity - 2,
            "price": item.price + 100
        }

        # Define order data
        order_data = {
            "client": client.name,
            "ordered_items": [ordered_item_data, ordered_item_2_data]
        }

        # Mock the Client Ordered Item serializer to verify it's called
        ordered_item_serializer_path = "apps.client_orders.serializers.ClientOrderedItemSerializer"
        with patch(ordered_item_serializer_path) as mock_ordered_item_serializer:
            # Mock instance of the Client Ordered Item serializer
            mock_ordered_item_instance = mock_ordered_item_serializer.return_value
            mock_ordered_item_instance.is_valid.return_value = True

            # Call the Client Order serializer
            serializer = ClientOrderSerializer(
                data=order_data,
                context={'user': user}
            )
            assert serializer.is_valid(), serializer.errors

            order = serializer.save()

            assert str(order.client.id) == str(client.id)

            # Verify Client Ordered Item serializer was called twice
            assert mock_ordered_item_serializer.call_count == 2

            # Add order to the ordered items data
            ordered_item_data["order"] = order.id
            ordered_item_2_data["order"] = order.id

            # Verify Client Ordered Item serializer was called twice
            # with each ordered item data
            mock_ordered_item_serializer.assert_any_call(
                data=ordered_item_data,
                context={"user": user}
            )

            mock_ordered_item_serializer.assert_any_call(
                data=ordered_item_2_data,
                context={"user": user}
            )

            # Verify save was called on the Client Ordered Item serializer
            assert mock_ordered_item_instance.save.call_count == 2

    def test_order_creation_creates_new_shipping_address_if_not_exists(
        self,
        user,
        item,
        location_data,
        pending_status
    ):
        # Verify location does not exist before order creation
        assert not Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).exists()

        # Define order data with the inexistent location data
        client = ClientFactory.create(created_by=user)
        order_data = {
            "client": client.name,
            "ordered_items": [
                {
                    "item": item.name,
                    "ordered_quantity": item.quantity - 2,
                    "ordered_price": item.price + 100
                }
            ],
            "shipping_address": location_data,
            "delivery_status": pending_status.name,
            "payment_status": pending_status.name
        }

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.shipping_address is not None

        # Verify location has been created and set to order after order creation
        location = Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).first()
        assert location is not None
        assert str(order.shipping_address.id) == str(location.id)

    def test_order_creation_retrieves_existing_shipping_address(
        self,
        user,
        location,
        order_data
    ):
        initial_location_count = Location.objects.count()

        # Set for order's shipping_address the same existing location's data
        order_data["shipping_address"] = {
            "country": location.country.name,
            "city": location.city.name,
            "street_address": location.street_address
        }

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.shipping_address is not None

        # Verify the order's shipping_address was set to 
        # the exact existing location
        assert str(order.shipping_address.id) == str(location.id)

        # Verify no new location was created
        assert Location.objects.count() == initial_location_count

    def test_order_creation_uses_location_serializer(
        self,
        user,
        client,
        ordered_item_data,
        location_data
    ):
        order_data = {
            "client": client.name,
            "ordered_items": [ordered_item_data],
            "shipping_address": location_data
        }

        # Mock the location serializer to verify it's called
        location_serializer_path = "apps.client_orders.serializers.LocationSerializer"
        with patch(location_serializer_path) as mock_location_serializer:
            # Mock instance of the location serializer
            mock_location_instance = mock_location_serializer.return_value
            mock_location_instance.is_valid.return_value = True
            mock_location_instance.save.return_value = LocationFactory.create()

            # Call the Client Order serializer
            serializer = ClientOrderSerializer(
                data=order_data,
                context={'user': user}
            )
            assert serializer.is_valid()

            order = serializer.save()

            assert str(order.client.id) == str(client.id)

            # Verify location serializer was called with the correct data
            mock_location_serializer.assert_called_once_with(
                data=location_data,
                context={'user': user}
            )

            # Verify save was called on the location serializer
            mock_location_instance.save.assert_called_once()

            # Verify the created location was linked to the order
            assert (
                order.shipping_address ==
                mock_location_instance.save.return_value
            )

    def test_order_creation_retrieves_existing_source_by_name(
        self,
        user,
        order_data,
        source,
    ):
        initial_acq_source_count = AcquisitionSource.objects.count()

        order_data["source"] = source.name
        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.source is not None
        assert str(order.source.id) == str(source.id)

        # Verify no new acq source was created
        assert AcquisitionSource.objects.count() == initial_acq_source_count

    def test_order_creation_creates_new_source_if_not_exists(
        self,
        user,
        item,
        pending_status
    ):
        # Verify acq source does not exist before order creation
        assert not AcquisitionSource.objects.filter(name__iexact="ADS").exists()

        # Define order data with the inexistent source name
        client = ClientFactory.create(created_by=user)
        order_data = {
            "client": client.name,
            "ordered_items": [
                {
                    "item": item.name,
                    "ordered_quantity": item.quantity - 2,
                    "ordered_price": item.price + 100
                }
            ],
            "source": "ADS",
            "delivery_status": pending_status.name,
            "payment_status": pending_status.name
        }

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        order = serializer.save()
        assert order.source is not None

        # Verify acq source has been created and set for order after order creation
        source = AcquisitionSource.objects.filter(name__iexact="ADS").first()
        assert source is not None
        assert str(order.source.id) == str(source.id)

    def test_order_serializer_retrieves_delivery_and_payment_status_by_name(
        self,
        user,
        pending_status,
        order_data
    ):
        order_data["delivery_status"] = pending_status.name
        order_data["payment_status"] = pending_status.name

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert str(order.delivery_status.id) == str(pending_status.id)
        assert str(order.payment_status.id) == str(pending_status.id)

    def test_order_status_is_set_to_pending_by_default(self, user, order_data):
        # Remove delivery and payment status from order_data
        order_data.pop("delivery_status")
        order_data.pop("payment_status")

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        # Verify delivery and payment status have been set to Pending for order
        assert order.delivery_status is not None
        assert order.payment_status is not None
        assert order.delivery_status.name == "Pending"
        assert order.payment_status.name == "Pending"

    def test_delivered_order_creates_a_sale_instance_with_orders_data(
        self,
        user,
        order_data,
        delivered_status
    ):
        order_data["delivery_status"] = delivered_status.name

        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.delivery_status.name == "Delivered"
        assert order.sale is not None

        sale = order.sale
        assert isinstance(sale, Sale)
        assert str(sale.client.id) == str(order.client.id)
        assert str(sale.shipping_address.id) == str(order.shipping_address.id)
        assert str(sale.source.id) == str(order.source.id)
        assert str(sale.delivery_status.id) == str(order.delivery_status.id)
        assert str(sale.payment_status.id) == str(order.payment_status.id)
        assert len(sale.sold_items.all()) == len(order.ordered_items.all())

        # Verify that both sale and order items are the same
        sale_items = [
            {"item": sold_item.item.name,
             "quantity": sold_item.sold_quantity,
             "price": sold_item.sold_price}
            for sold_item
            in sale.sold_items.all()
        ]
        sale_items_set = {frozenset(item.items()) for item in sale_items}
        order_items = [
            {"item": ordered_item.item.name,
             "quantity": ordered_item.ordered_quantity,
             "price": ordered_item.ordered_price}
            for ordered_item
            in order.ordered_items.all()
        ]
        order_items_set = {frozenset(item.items()) for item in order_items}
        assert sale_items_set == order_items_set

    def test_order_creation_registers_a_new_activity(self, user, order_data):
        serializer = ClientOrderSerializer(
            data=order_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        order = serializer.save()

        assert Activity.objects.filter(
            action="created",
            model_name="client order",
            object_ref__contains=order.reference_id
        ).exists()

    def test_order_update(self, user, client_order, order_data):
        order_delivery_status = client_order.delivery_status.name
        order_tracking_number = client_order.tracking_number

        shipped_status = OrderStatusFactory.create(name="Shipped")
        order_data["delivery_status"] = shipped_status.name
        order_data["tracking_number"] = "L268DL246"

        serializer = ClientOrderSerializer(
            client_order,
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid()

        order_update = serializer.save()
        assert order_update.delivery_status.name != order_delivery_status
        assert order_update.tracking_number != order_tracking_number

    def test_order_partial_update(self, user, client_order):
        order_tracking_number = client_order.tracking_number

        serializer = ClientOrderSerializer(
            client_order,
            data={"tracking_number": "L268DL246"},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        order_update = serializer.save()
        assert order_update.tracking_number != order_tracking_number

    def test_client_update_fails_for_delivered_orders(
        self,
        user,
        client_order,
        delivered_status,
        ordered_item
    ):
        # Update order status to delivered
        client_order.delivery_status = delivered_status
        client_order.save()

        # Create new client
        client = ClientFactory.create(created_by=user, name="Safuan")

        # Try to update order with a new value for the client field
        serializer = ClientOrderSerializer(
            client_order,
            data={"client": client.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        # Verify a ValidationError is raised when we try to save/update the order
        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This order and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "client" in error_data["restricted_fields"]

    def test_ordered_items_update_fails_for_delivered_orders(
        self,
        user,
        client_order,
        delivered_status,
        ordered_item
    ):
        # Update order status to delivered
        client_order.delivery_status = delivered_status
        client_order.save()

        # Get order's data
        order_data = ClientOrderSerializer(client_order).data

        # Remove 'total_price' and 'total_profit' from ordered_items data
        keys_to_remove_from_items = ['total_price', 'total_profit']
        ordered_items = []
        for item in order_data["ordered_items"]:
            ordered_items.append(
                {key: value for key,
                 value in item.items()
                 if key not in keys_to_remove_from_items}
            )
        ordered_items_set = {frozenset(item.items()) for item in ordered_items}

        # Define new ordered items
        new_ordered_items = [
            {
                "item": "DataShow",
                "ordered_quantity": 4,
                "ordered_price": 500
            }
        ]
        new_ordered_items_set = {
            frozenset(item.items())
            for item in new_ordered_items
        }

        # Verify that new ordered items are different than order's ordered items
        assert new_ordered_items_set != ordered_items_set

        # Try to update order with new ordered items
        serializer = ClientOrderSerializer(
            client_order,
            data={"ordered_items": new_ordered_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        # Verify a ValidationError is raised when we try to save/update the order
        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This order and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "ordered_items" in error_data["restricted_fields"]

    def test_delivery_status_update_fails_for_delivered_orders(
        self,
        user,
        client_order,
        pending_status,
        delivered_status,
        ordered_item
    ):
        # Update order status to delivered
        client_order.delivery_status = delivered_status
        client_order.save()

        # Try to update order with a new value for the delivery_status field
        serializer = ClientOrderSerializer(
            client_order,
            data={"delivery_status": pending_status.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        # Verify a ValidationError is raised when we try to save/update the order
        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This order and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "delivery_status" in error_data["restricted_fields"]

    def test_ordered_items_update_removes_missing_items(self, user, client_order):
        # Create two items for the order
        items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        for item in items:
            ClientOrderedItemFactory.create(
                created_by=user,
                item=item,
                order=client_order
            )

        # Define new ordered items list
        new_items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        new_ordered_items = [
            {
                "item": item.name,
                "ordered_quantity": item.quantity - 1,
                "ordered_price": item.price + 100
            }
            for item in new_items
        ]

        # Call the ClientOrderSerializer to update order's ordered_items
        serializer = ClientOrderSerializer(
            client_order,
            data={"ordered_items": new_ordered_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify the length of the order's new ordered_items
        ordered_items_update = order_update.ordered_items.all()
        assert ordered_items_update.count() == 2
        assert len(ordered_items_update) == len(new_ordered_items)

        updated_items_ids = [
            str(ordered_item.item.id)
            for ordered_item
            in ordered_items_update
        ]

        # Verify that the new items have been added to the order ordered items
        assert all(str(item.id) in updated_items_ids for item in new_items)

        # Verify that the old items have been excluded from the order's
        # ordered items list
        assert all(str(item.id) not in updated_items_ids for item in items)

    def test_ordered_items_update_keeps_and_updates_existing_items(
        self,
        user,
        client_order
    ):
        # Create two items for the order
        items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        ordered_item_1 = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order,
            item=items[0]
        )
        ordered_item_2 = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order,
            item=items[1]
        )

        # Define new ordered items list
        new_items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        new_ordered_items = [
            {
                "item": item.name,
                "ordered_quantity": item.quantity - 1,
                "ordered_price": item.price + 100
            }
            for item in new_items
        ]

        # Add ordered_item_1 to the new ordered items list
        # with different ordered_quantity and ordered_price
        new_ordered_items.append({
            "item": ordered_item_1.item.name,
            "ordered_quantity": ordered_item_1.ordered_quantity - 1,
            "ordered_price": ordered_item_1.ordered_price + 100,
        })

        # Call the ClientOrderSerializer to update order's ordered_items
        serializer = ClientOrderSerializer(
            client_order,
            data={"ordered_items": new_ordered_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify the length of the order's new ordered_items
        ordered_items_update = order_update.ordered_items.all()
        assert ordered_items_update.count() == 3
        assert len(ordered_items_update) == len(new_ordered_items)

        updated_items_ids = [
            str(ordered_item.item.id)
            for ordered_item
            in ordered_items_update
        ]

        # Verify that the new items have been added to the order ordered items
        assert all(str(item.id) in updated_items_ids for item in new_items)

        # Verify that ordered_item_1 remained in the order's ordered items list
        # and that its quantity and price got updated
        exiting_item = order_update.ordered_items.filter(
            item__id=ordered_item_1.item.id
        ).first()
        assert exiting_item is not None
        assert str(exiting_item.item.id) in updated_items_ids
        assert exiting_item.ordered_quantity == ordered_item_1.ordered_quantity - 1
        assert exiting_item.ordered_price == ordered_item_1.ordered_price + 100

        # Verify that ordered_item_2 has been excluded from
        # the order's ordered items list
        assert str(ordered_item_2.item.id) not in updated_items_ids

    def test_order_update_removes_optional_field_if_set_to_none(
        self,
        user,
        client_order,
    ):
        assert client_order.shipping_address is not None
        assert client_order.source is not None

        serializer = ClientOrderSerializer(
            client_order,
            data={
                "shipping_address": None,
                "source": None, 
            },
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()
        assert order_update.updated
        assert client_order.shipping_address is None
        assert client_order.source is None

    def test_order_status_update_to_delivered_creates_a_sale_with_orders_data(
        self,
        user,
        client_order,
        delivered_status
    ):
        assert client_order.delivery_status.name != delivered_status.name
        assert client_order.sale is None

        serializer = ClientOrderSerializer(
            client_order,
            data={"delivery_status": delivered_status.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()
        assert order_update.sale is not None

        sale = order_update.sale
        assert isinstance(sale, Sale)
        assert str(sale.client.id) == str(order_update.client.id)
        assert str(sale.shipping_address.id) == str(order_update.shipping_address.id)
        assert str(sale.source.id) == str(order_update.source.id)
        assert str(sale.delivery_status.id) == str(order_update.delivery_status.id)
        assert str(sale.payment_status.id) == str(order_update.payment_status.id)
        assert len(sale.sold_items.all()) == len(order_update.ordered_items.all())

    def test_changes_to_order_reflect_to_linked_sale(
        self,
        user,
        client_order,
        delivered_status,
        ordered_item
    ):
        # Change order delivery status to delivered to create a linked sale
        assert client_order.delivery_status.name != delivered_status.name
        assert client_order.sale is None
        serializer = ClientOrderSerializer(
            client_order,
            data={"delivery_status": delivered_status.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors
        order_update = serializer.save()
        
        # Verify that a sale has been created with order's data
        assert order_update.sale is not None
        sale = order_update.sale
        assert str(sale.source.id) == str(order_update.source.id)

        # Update order's source of acquisition
        emailing_source = AcquisitionSourceFactory.create(
            added_by=user,
            name="Emailing"
        )
        serializer = ClientOrderSerializer(
            client_order,
            data={"source": emailing_source.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()
        sale = order_update.sale

        # Verify that source has been updated for both order and sale
        assert str(order_update.source.id) == str(emailing_source.id)
        assert str(order_update.source.id) == str(sale.source.id)

    def test_order_serializer_data_fields(self, client_order):
        serializer = ClientOrderSerializer(client_order)

        expected_fields = {
            "id",
            "reference_id",
            "created_by",
            "client",
            "ordered_items",
            "delivery_status",
            "payment_status",
            "tracking_number",
            "shipping_address",
            "shipping_cost",
            "net_profit",
            "source",
            "linked_sale",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(serializer.data.keys())

    def test_order_serializer_data_fields_types(
        self,
        client_order,
        sale,
        ordered_item
    ):
        client_order.sale = sale
        client_order.save()

        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert type(order_data["id"]) == str
        assert type(order_data["reference_id"]) == str
        assert type(order_data["created_by"]) == str
        assert type(order_data["client"]) == str
        assert type(order_data["ordered_items"]) == list
        assert type(order_data["delivery_status"]) == str
        assert type(order_data["payment_status"]) == str
        assert type(order_data["tracking_number"]) == str
        assert type(order_data["shipping_address"]) == dict
        assert type(order_data["shipping_cost"]) == float
        assert type(order_data["net_profit"]) == float
        assert type(order_data["source"]) == str
        assert type(order_data["linked_sale"]) == str
        assert type(order_data["created_at"]) == str
        assert type(order_data["updated_at"]) == str
        assert type(order_data["updated"]) == bool

    def test_order_serializer_general_fields_data(self, client_order):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert order_data["id"] == str(client_order.id)
        assert order_data["reference_id"] == client_order.reference_id
        assert order_data["created_by"] == client_order.created_by.username
        assert order_data["created_at"] == date_repr_format(client_order.created_at)
        assert order_data["updated_at"] == date_repr_format(client_order.updated_at)
        assert order_data["updated"] == client_order.updated

    def test_order_serializer_client_and_source_fields_data(self, client_order):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert order_data["client"] == client_order.client.name
        assert order_data["source"] == client_order.source.name

    def test_order_serializer_ordered_items_field_data(self, client_order, ordered_item):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert len(order_data["ordered_items"]) == 1
        ordered_item_data = order_data["ordered_items"][0]
        assert ordered_item_data["item"] == ordered_item.item.name
        assert ordered_item_data["ordered_quantity"] == ordered_item.ordered_quantity
        assert ordered_item_data["ordered_price"] == ordered_item.ordered_price
        assert ordered_item_data["total_price"] == ordered_item.total_price
        assert ordered_item_data["total_profit"] == ordered_item.total_profit

    def test_order_serializer_status_and_tracking_fields_data(self, client_order):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert order_data["delivery_status"] == client_order.delivery_status.name
        assert order_data["payment_status"] == client_order.payment_status.name
        assert order_data["tracking_number"] == client_order.tracking_number

    def test_order_serializer_shipping_address_field_data(self, client_order):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        shipping_address = order_data["shipping_address"]
        assert shipping_address["country"] == client_order.shipping_address.country.name
        assert shipping_address["city"] == client_order.shipping_address.city.name
        assert shipping_address["street_address"] == client_order.shipping_address.street_address

    def test_order_serializer_financial_fields_data(self, client_order):
        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert order_data["shipping_cost"] == float(client_order.shipping_cost)
        assert order_data["net_profit"] == float(client_order.net_profit)

    def test_order_serializer_linked_sale_field_data(self, client_order, sale):
        client_order.sale = sale
        client_order.save()

        serializer = ClientOrderSerializer(client_order)
        order_data = serializer.data

        assert order_data["linked_sale"] is not None
        assert order_data["linked_sale"] == str(client_order.sale.id)
        assert order_data["linked_sale"] == str(sale.id)
