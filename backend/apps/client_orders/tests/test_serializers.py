import pytest
from utils.serializers import default_datetime_str_format
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
