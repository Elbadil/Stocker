import pytest
from unittest.mock import patch
from utils.serializers import default_datetime_str_format
from apps.base.models import Activity
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
    ClientOrderFactory,
    ClientOrderedItemFactory
)


@pytest.fixture
def location_data(city, country):
    return {
        "country": country.name,
        "city": city.name,
        "street_address": "5th avenue"
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

    def test_order_status_serializer_data_fields(self, order_status):
        serializer = OrderStatusSerializer(order_status)

        assert "id" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_order_status_serializer_data_fields_types(self, order_status):
        serializer = OrderStatusSerializer(order_status)
        order_status_data = serializer.data

        assert type(order_status_data["id"]) == str
        assert type(order_status_data["name"]) == str
        assert type(order_status_data["created_at"]) == str
        assert type(order_status_data["updated_at"]) == str

    def test_order_status_serializer_data(self, order_status):
        serializer = OrderStatusSerializer(order_status)
        order_status_data = serializer.data
    
        assert order_status_data["id"] == order_status.id
        assert order_status_data["name"] == "Pending"
        assert (
            order_status_data["created_at"] ==
            default_datetime_str_format(order_status.created_at)
        )
        assert (
            order_status_data["updated_at"] ==
            default_datetime_str_format(order_status.updated_at)
        )

    def test_order_status_update(self, order_status):
        order_status_name = order_status.name

        serializer = OrderStatusSerializer(order_status, data={"name": "Failed"})
        assert serializer.is_valid()

        order_status_update = serializer.save()
        assert order_status_update.name == "Failed"
        assert order_status_update.name != order_status_name


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
    
    def test_client_creation_creates_the_provided_location(
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

        # Verify location has been created after client creation
        assert Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).exists()

    def test_client_creation_retrieves_existing_location(
        self,
        user,
        location
    ):
        initial_location_count = Location.objects.count()

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

    def test_client_creation_creates_the_provided_source(
        self,
        user,
    ):
        # Verify acq source does not exist before client creation
        assert not AcquisitionSource.objects.filter(name__iexact="ADS").exists()

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
        assert AcquisitionSource.objects.filter(name__iexact="ADS").exists()

    def test_client_creation_retrieves_existing_source(
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

        # Verify no new location was created
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
            data={"age": 27},
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
