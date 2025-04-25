import pytest
from unittest.mock import patch
from rest_framework.exceptions import ValidationError
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.inventory.models import Item
from apps.inventory.factories import ItemFactory
from apps.client_orders.models import Location
from apps.client_orders.factories import LocationFactory
from apps.supplier_orders.models import (
    Supplier,
    SupplierOrderedItem
)
from apps.supplier_orders.serializers import (
    SupplierSerializer,
    SupplierOrderedItemSerializer
)
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderFactory,
    SupplierOrderedItemFactory
)
from utils.serializers import (
    get_location,
    date_repr_format,
    decimal_to_float
)


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


@pytest.mark.django_db
class TestSupplierOrderedItemSerializer:
    """Tests for the SupplierOrderedItemSerializer"""

    def test_ordered_item_serializer_sets_created_by_from_context(
        self,
        user,
        ordered_item_data
    ):
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        item = serializer.save()
        assert item.created_by is not None
        assert str(item.created_by.id) == str(user.id)

    def test_ordered_item_creation_fails_without_item_name(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop('item')
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'item' in serializer.errors
        assert "This field is required." in serializer.errors['item']

    def test_ordered_item_creation_fails_without_supplier_name(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop('supplier')
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'supplier' in serializer.errors
        assert "This field is required." in serializer.errors['supplier']
    
    def test_ordered_item_creation_fails_with_non_existing_supplier_name(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data["supplier"] = "supplier 3"

        # Verify that the supplier name does not exist
        assert not Supplier.objects.filter(
            created_by=user,
            name="supplier 3"
        ).exists()

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'supplier' in serializer.errors
        assert serializer.errors['supplier'] == [
            ("Supplier 'supplier 3' does not exist. "
             "Please create a new supplier if this is a new entry.")
        ]

    def test_ordered_item_creation_fails_with_non_owned_supplier_name(
        self,
        user,
        ordered_item_data
    ):
        # Create a different user and link it to a supplier
        user_2 = UserFactory.create(username="user_2")
        supplier = SupplierFactory.create(created_by=user_2)

        # Assign the ordered item data to the supplier's name not owned by the context user
        ordered_item_data["supplier"] = supplier.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'supplier' in serializer.errors
        assert serializer.errors['supplier'] == [
            (f"Supplier '{supplier.name}' does not exist. "
             "Please create a new supplier if this is a new entry.")
        ]

    def test_ordered_item_creation_fails_without_quantity(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop('ordered_quantity')
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'ordered_quantity' in serializer.errors
        assert "This field is required." in serializer.errors['ordered_quantity']

    def test_ordered_item_creation_fails_with_quantity_less_than_one(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data["ordered_quantity"] = 0
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'ordered_quantity' in serializer.errors
        assert (
            "Ensure this value is greater than or equal to 1."
            in serializer.errors['ordered_quantity']
        )

    def test_ordered_item_creation_fails_without_price(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop('ordered_price')
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'ordered_price' in serializer.errors
        assert "This field is required." in serializer.errors['ordered_price']

    def test_ordered_item_creation_fails_with_negative_price(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data["ordered_price"] = -1
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'ordered_price' in serializer.errors
        assert (
            "Ensure this value is greater than or equal to 0.0."
            in serializer.errors['ordered_price']
        )

    def test_ordered_item_creation_fails_without_order_id(
        self,
        user,
        ordered_item_data
    ):
        ordered_item_data.pop('order')
        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()
        assert 'order' in serializer.errors
        assert "This field is required." in serializer.errors['order']

    def test_ordered_item_creation_fails_for_delivered_orders(
        self,
        user,
        ordered_item_data,
        supplier_order,
        delivered_status
    ):
        # Update order's delivery status to delivered
        supplier_order.delivery_status = delivered_status
        supplier_order.save()

        ordered_item_data["order"] = supplier_order.id

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert 'order' in errors.value.detail
        assert errors.value.detail["order"] == (
            f"Cannot apply changes to the order "
            f"with ID '{supplier_order.id}' ordered items "
            "because it has already been marked as Delivered. "
            f"Changes to delivered orders are restricted "
            "to maintain data integrity."
        )

    def test_ordered_item_creation_retrieves_existing_item_with_same_supplier(
        self,
        user,
        ordered_item_data,
        supplier,
        item
    ):
        # Update item supplier
        item.supplier = supplier
        item.save()

        ordered_item_data["item"] = item.name
        ordered_item_data["supplier"] = item.supplier.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors
        ordered_item = serializer.save()

        # Verify that the ordered item has the correct item and supplier
        assert str(ordered_item.item.id)== str(item.id)
        assert str(ordered_item.supplier.id)== str(item.supplier.id)

    def test_ordered_item_creation_creates_new_item_instance_if_not_exists(
        self,
        user,
        ordered_item_data
    ):
        # Verify that item name in ordered item data does not exist
        assert not Item.objects.filter(name__iexact=ordered_item_data["item"]).exists()

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()
        ordered_item = serializer.save()
        assert ordered_item.item.name == ordered_item_data["item"]
        assert ordered_item.supplier.name == ordered_item_data["supplier"]

        # Verify that a new item has been created with ordered item data
        assert Item.objects.filter(
            created_by=ordered_item.created_by,
            supplier=ordered_item.supplier,
            name=ordered_item.item.name,
            quantity=ordered_item.ordered_quantity,
            price=ordered_item.ordered_price
        ).exists()

    def test_ordered_item_creation_with_existing_item_without_supplier(
        self,
        user,
        ordered_item_data,
        supplier,
    ):
        # Create an item without a supplier
        item = ItemFactory.create(
            created_by=user,
            supplier=None,
            in_inventory=True,
        )
        assert item.supplier is None

        # Set ordered item's data to match the item
        ordered_item_data["item"] = item.name
        ordered_item_data["supplier"] = supplier.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()
        ordered_item = serializer.save()
        assert str(ordered_item.item.id)== str(item.id)
        assert str(ordered_item.supplier.id) == str(supplier.id)

        # Verify that existing item's supplier has been set to ordered item's supplier
        item.refresh_from_db()
        assert str(item.supplier.id) == str(ordered_item.supplier.id)

    def test_ordered_item_creation_fails_for_exiting_item_with_different_supplier(
        self,
        user,
        ordered_item_data,
    ):
        # Create an item and link it to a supplier
        supplier_1 = SupplierFactory.create(created_by=user, name="Supplier 1")
        item = ItemFactory.create(
            created_by=user,
            in_inventory=True,
            supplier=supplier_1
        )
        
        # Create a different supplier
        supplier_2 = SupplierFactory.create(created_by=user, name="Supplier 2")

        # Set ordered item's data to match the item and not it's supplier
        ordered_item_data["item"] = item.name
        ordered_item_data["supplier"] = supplier_2.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert 'item' in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{item.name}' is associated "
             "with another supplier."
        )

    def test_ordered_item_creation_fails_with_different_supplier_from_order(
        self,
        user,
        ordered_item_data,
        supplier_order,
    ):
        # Create a different supplier
        supplier_2 = SupplierFactory.create(created_by=user, name="Supplier 2")
        
        # Verify that the newly created supplier is different from the order's supplier
        assert str(supplier_2.id) != str(supplier_order.supplier.id)

        # Set ordered item's data with the order and the different supplier
        ordered_item_data["order"] = supplier_order.id
        ordered_item_data["supplier"] = supplier_2.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert 'supplier' in errors.value.detail
        assert errors.value.detail["supplier"] == (
            f"Order's supplier '{supplier_order.supplier.name}' does "
            f"not match the selected supplier '{supplier_2.name}'."
        )

    def test_ordered_item_creation_fails_with_item_already_in_order(
        self,
        user,
        ordered_item_data,
        supplier_order,
        item
    ):
        # Add an ordered item to the order
        SupplierOrderedItemFactory.create(
            created_by=user,
            order=supplier_order,
            item=item
        )

        # Set ordered item's data with the same item as
        # the existing ordered item in order
        ordered_item_data["order"] = supplier_order.id
        ordered_item_data["item"] = item.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert 'item' in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{item.name}' already exists in the order's list of ordered items. "
             "Consider updating the existing item if you need to modify its details."
        )

    def test_ordered_item_creation_succeeds(
        self,
        user,
        ordered_item_data,
        supplier_order,
        item
    ):
        ordered_item_data["order"] = supplier_order.id
        ordered_item_data["item"] = item.name

        serializer = SupplierOrderedItemSerializer(
            data=ordered_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()
        ordered_item = serializer.save()

        assert SupplierOrderedItem.objects.filter(
            created_by=ordered_item.created_by,
            order=ordered_item.order,
            item=ordered_item.item,
            ordered_quantity=ordered_item.ordered_quantity,
            ordered_price=ordered_item.ordered_price
        ).exists()

    def test_ordered_item_update(
        self,
        user,
        ordered_item_data,
        ordered_item
    ):
        # Initial ordered item quantity
        ordered_quantity = ordered_item.ordered_quantity

        # Set new ordered quantity
        ordered_item_data["ordered_quantity"] = ordered_quantity + 1

        serializer = SupplierOrderedItemSerializer(
            instance=ordered_item,
            data=ordered_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()
        ordered_item_update = serializer.save()

        assert ordered_item_update.ordered_quantity != ordered_quantity
        assert ordered_item_update.ordered_quantity == ordered_quantity + 1

    def test_ordered_item_partial_update(
        self,
        user,
        ordered_item
    ):
        # Initial ordered item quantity
        ordered_quantity = ordered_item.ordered_quantity

        serializer = SupplierOrderedItemSerializer(
            instance=ordered_item,
            data={"ordered_quantity": ordered_quantity + 1},
            context={'user': user},
            partial=True
        )

        assert serializer.is_valid()
        ordered_item_update = serializer.save()

        assert ordered_item_update.ordered_quantity != ordered_quantity
        assert ordered_item_update.ordered_quantity == ordered_quantity + 1

    def test_ordered_item_serializer_data_fields(self, ordered_item):
        serializer = SupplierOrderedItemSerializer(ordered_item)

        expected_fields = {
            "id",
            "created_by",
            "order",
            "supplier",
            "item",
            "ordered_quantity",
            "ordered_price",
            "in_inventory",
            "total_price",
            "created_at",
            "updated_at"
        }

        assert expected_fields.issubset(serializer.data.keys())

    def test_ordered_item_serializer_data_fields_types(self, ordered_item):
        serializer = SupplierOrderedItemSerializer(ordered_item)
        ordered_item_data = serializer.data

        assert type(ordered_item_data["id"]) == str
        assert type(ordered_item_data["created_by"]) == str
        assert type(ordered_item_data["order"]) == str
        assert type(ordered_item_data["supplier"]) == str
        assert type(ordered_item_data["item"]) == str
        assert type(ordered_item_data["ordered_quantity"]) == int
        assert type(ordered_item_data["ordered_price"]) == float
        assert type(ordered_item_data["in_inventory"]) == bool
        assert type(ordered_item_data["total_price"]) == float
        assert type(ordered_item_data["created_at"]) == str
        assert type(ordered_item_data["updated_at"]) == str

    def test_ordered_item_serializer_data_fields_values(self, ordered_item):
        serializer = SupplierOrderedItemSerializer(ordered_item)
        ordered_item_data = serializer.data

        assert str(ordered_item_data["id"]) == str(ordered_item.id)
        assert ordered_item_data["created_by"] == ordered_item.created_by.username
        assert str(ordered_item_data["order"]) == str(ordered_item.order.id)
        assert ordered_item_data["supplier"] == ordered_item.supplier.name
        assert ordered_item_data["item"] == ordered_item.item.name
        assert ordered_item_data["ordered_quantity"] == ordered_item.ordered_quantity
        assert ordered_item_data["ordered_price"] == decimal_to_float(ordered_item.ordered_price)
        assert ordered_item_data["in_inventory"] == ordered_item.in_inventory
        assert ordered_item_data["total_price"] == decimal_to_float(ordered_item.total_price)
        assert ordered_item_data["created_at"] == date_repr_format(ordered_item.created_at)
        assert ordered_item_data["updated_at"] == date_repr_format(ordered_item.updated_at)

