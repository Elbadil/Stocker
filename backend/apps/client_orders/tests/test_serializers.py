import pytest
from utils.serializers import default_datetime_str_format
from apps.client_orders.models import Country, City, Location
from apps.client_orders.serializers import (
    CountrySerializer,
    CitySerializer,
    LocationSerializer,
    AcquisitionSource,
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

        category = serializer.save()
        assert category.name == "Morocco"
    
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

    def test_location_creation_retrieves_country_and_city_by_name(
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
        # Create a location without a user in the serializer's context
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

        assert location_1.country.name == location_data["country"]
        assert location_1.city.name == location_data["city"]
        assert location_1.street_address == location_data["street_address"]

        # Create another location with the same attributes
        serializer = LocationSerializer(data=location_data)
        assert serializer.is_valid()

        location_2 = serializer.save()

        # Ensure no additional location with the same attributes
        # has been created
        assert str(location_1.id) == str(location_2.id)
        assert Location.objects.filter(
            country=country,
            city=city,
            street_address="5th avenue"
        ).count() == 1

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
