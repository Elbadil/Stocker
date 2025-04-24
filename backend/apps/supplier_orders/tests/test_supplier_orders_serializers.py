from unittest.mock import patch
import pytest
from apps.base.models import Activity
from apps.client_orders.models import Location
from apps.client_orders.factories import LocationFactory
from apps.supplier_orders.serializers import SupplierSerializer
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderFactory,
    SupplierOrderedItemFactory
)
from utils.serializers import get_location, date_repr_format


@pytest.mark.django_db
class TestSupplierSerializer:
    """Tests for the SupplierSerializer"""

    def test_supplier_serializer_sets_created_by_from_context(self, user):
        serializer = SupplierSerializer(
            data={"name": "Supplier 1"},
            context={'user': user}
        )
        assert serializer.is_valid()

        supplier = serializer.save()
        assert supplier.created_by is not None
        assert str(supplier.created_by.id) == str(user.id)

    def test_supplier_creation_fails_without_name(self):
        serializer = SupplierSerializer(data={})
        assert not serializer.is_valid()

        assert "name" in serializer.errors
        assert "This field is required." in serializer.errors["name"]
    
    def test_supplier_creation_fails_with_blank_name(self):
        serializer = SupplierSerializer(data={"name": " "})
        assert not serializer.is_valid()

        assert "name" in serializer.errors
        assert "This field may not be blank." in serializer.errors["name"]

    def tets_supplier_creation_fails_with_duplicate_name(self):
        SupplierFactory.create(name="Supplier 1")
        serializer = SupplierSerializer(data={"name": "Supplier 1"})
        assert not serializer.is_valid()

        assert "name" in serializer.errors
        assert "Supplier with this name already exists." in serializer.errors["name"]

    def test_supplier_creation_fails_with_invalid_email(self):
        serializer = SupplierSerializer(
            data={
                "name": "Supplier 1",
                "email": "invalid_email"
            }
        )
        assert not serializer.is_valid()

        assert "email" in serializer.errors
        assert "Enter a valid email address." in serializer.errors["email"]

    def test_supplier_creation_creates_new_location_if_not_exists(
        self,
        user,
        location_data
    ):
        # Verify location does not exist before supplier creation
        assert not Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).exists()

        serializer = SupplierSerializer(
            data={
                "name": "Supplier 1",
                "location": location_data
            },
            context={'user': user}
        )
        assert serializer.is_valid()

        supplier = serializer.save()
        assert supplier.location is not None

        # Verify location has been created and set to supplier after supplier creation
        location = Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).first()
        assert location is not None
        assert str(supplier.location.id) == str(location.id)

    def test_supplier_creation_retrieves_existing_location(
        self,
        user,
        location
    ):
        initial_location_count = Location.objects.count()

        # Set for supplier's location the same existing location's data
        supplier_data = {
            "name": "Supplier 1",
            "location": {
                "country": location.country.name,
                "city": location.city.name,
                "street_address": location.street_address
            }
        }

        serializer = SupplierSerializer(
            data=supplier_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        supplier = serializer.save()
        assert supplier.location is not None

        # Verify the supplier's location was set to the exact 
        # existing location
        assert str(supplier.location.id) == str(location.id)

        # Verify no new location has been created
        assert Location.objects.count() == initial_location_count

    def test_supplier_creation_uses_location_serializer(self, user, location_data):
        supplier_data = {
            "name": "Supplier 1",
            "location": location_data
        }

        # Mock the location serializer to verify it's called
        location_serializer_path = "apps.client_orders.serializers.LocationSerializer"
        with patch(location_serializer_path) as mock_location_serializer:
            # Mock instance of the location serializer
            mock_location_instance = mock_location_serializer.return_value
            mock_location_instance.is_valid.return_value = True
            mock_location_instance.save.return_value = LocationFactory.create()

            # Call the supplier serializer
            serializer = SupplierSerializer(
                data=supplier_data,
                context={'user': user}
            )
            assert serializer.is_valid()

            supplier = serializer.save()
            assert supplier.location is not None

            # Verify location serializer was called with the correct data
            mock_location_serializer.assert_called_once_with(
                data=location_data,
                context={'user': user}
            )

            # Verify save was called on the location serializer
            mock_location_instance.save.assert_called_once()

            # Verify the created location was linked to the supplier
            assert (
                str(supplier.location.id) ==
                str(mock_location_instance.save.return_value.id)
            )

    def test_supplier_creation_registers_a_new_activity(self, user):
        serializer = SupplierSerializer(
            data={"name": "Supplier 1"},
            context={'user': user}
        )
        assert serializer.is_valid()

        supplier = serializer.save()
        assert supplier.created_by is not None
        assert supplier.name == "Supplier 1"
        assert str(supplier.created_by.id) == str(user.id)

        # Verify a new activity has been created
        assert Activity.objects.filter(
            action="created",
            model_name="supplier",
            object_ref__contains="Supplier 1"
        ).exists()

    def test_supplier_update(self, user, supplier):
        supplier_name = supplier.name

        serializer = SupplierSerializer(
            supplier,
            data={"name": "Safuan"},
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        supplier_update = serializer.save()
        assert supplier_update.name != supplier_name

    def test_supplier_partial_update(self, user, location):
        supplier = SupplierFactory.create(
            name="Supplier 1",
            created_by=user,
            location=location
        )
        supplier_name = supplier.name

        serializer = SupplierSerializer(
            supplier,
            data={"name": "Safuan"},
            context={'user': user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        supplier_update = serializer.save()
        assert supplier_update.name != supplier_name
        assert supplier_update.location is not None

    def test_supplier_update_removes_location_if_set_to_none(
        self,
        user,
        location
    ):
        supplier = SupplierFactory.create(
            name="Supplier 1",
            created_by=user,
            location=location
        )
        assert supplier.location is not None
    
        serializer = SupplierSerializer(
            supplier,
            data={"location": None},
            context={'user': user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        supplier_update = serializer.save()
        assert supplier_update.updated
        assert supplier_update.location is None

    def test_supplier_update_registers_a_new_activity(self, user, supplier):
        serializer = SupplierSerializer(
            supplier,
            data={"name": "Safuan"},
            context={'user': user}
        )
        assert serializer.is_valid()

        supplier_update = serializer.save()
        assert supplier_update.created_by is not None
        assert supplier_update.name == "Safuan"
        assert str(supplier_update.created_by.id) == str(user.id)

        # Verify a new activity has been created
        assert Activity.objects.filter(
            action="updated",
            model_name="supplier",
            object_ref__contains="Safuan"
        ).exists()

    def test_supplier_serializer_data_fields(self, supplier):
        serializer = SupplierSerializer(supplier)

        expected_fields = {
            "id",
            "created_by",
            "name",
            "phone_number",
            "email",
            "location",
            "total_orders",
            "created_by",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(serializer.data.keys())

    def test_supplier_serializer_data_fields_types(self, supplier):
        serializer = SupplierSerializer(supplier)

        assert type(serializer.data["id"]) == str
        assert type(serializer.data["created_by"]) == str
        assert type(serializer.data["name"]) == str
        assert type(serializer.data["phone_number"]) == str
        assert type(serializer.data["email"]) == str
        assert type(serializer.data["location"]) == dict
        assert type(serializer.data["total_orders"]) == int
        assert type(serializer.data["created_by"]) == str
        assert type(serializer.data["created_at"]) == str
        assert type(serializer.data["updated_at"]) == str
        assert type(serializer.data["updated"]) == bool

    def test_supplier_serializer_data_fields_values(self, supplier):
        serializer = SupplierSerializer(supplier)
        supplier_data = serializer.data

        assert str(supplier_data["id"]) == str(supplier.id)
        assert supplier_data["created_by"] == supplier.created_by.username
        assert supplier_data["name"] == supplier.name
        assert supplier_data["phone_number"] == supplier.phone_number
        assert supplier_data["email"] == supplier.email
        assert supplier_data["location"] == get_location(supplier.location)
        assert supplier_data["total_orders"] == supplier.total_orders
        assert supplier_data["created_at"] == date_repr_format(supplier.created_at)
        assert supplier_data["updated_at"] == date_repr_format(supplier.updated_at)
        assert supplier_data["updated"] == supplier.updated
