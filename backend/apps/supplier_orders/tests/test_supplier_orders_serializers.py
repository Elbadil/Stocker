import pytest
import copy
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
    SupplierOrderedItemSerializer,
    SupplierOrderSerializer
)
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderFactory,
    SupplierOrderedItemFactory
)
from apps.supplier_orders.utils import average_price
from utils.serializers import (
    get_location,
    date_repr_format,
    decimal_to_float
)
from utils.status import (
    DELIVERY_STATUS_OPTIONS_LOWER,
    PAYMENT_STATUS_OPTIONS_LOWER
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

    def test_ordered_item_update_validates_item_uniqueness_if_changed(
        self,
        user,
        ordered_item,
        supplier_order,
        supplier,
    ):
        # Create an item and add it to the order's ordered items
        item_pack = ItemFactory.create(
            created_by=user,
            supplier=supplier,
            name="Pack"
        )
        ordered_item_pack = SupplierOrderedItemFactory.create(
            created_by=user,
            supplier=supplier,
            order=supplier_order,
            item=item_pack
        )

        # Ensure both items belong to the same order
        assert str(ordered_item.order.id) == str(ordered_item_pack.order.id)

        # Attempt to update the ordered item's item
        # with the same name of the newly added item (ordered_item_pack)
        serializer = SupplierOrderedItemSerializer(
            ordered_item,
            data={"item": item_pack.name},
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        # Ensure ValidationError is raised for existing item in order's items list
        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert 'item' in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{item_pack.name}' already exists in the order's list of ordered items. "
             "Consider updating the existing item if you need to modify its details."
        )

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


@pytest.mark.django_db
class TestSupplierOrderSerializer:
    """Tests for the SupplierOrderSerializer"""

    def test_order_serializer_sets_created_by_from_context(self, user, order_data):
        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.created_by is not None
        assert str(order.created_by.id) == str(user.id)

    def test_order_creation_fails_without_supplier_name(self, user, order_data):
        order_data.pop("supplier")

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "supplier" in serializer.errors
        assert "This field is required." in serializer.errors["supplier"]

    def test_order_creation_fails_with_non_existing_supplier_name(self, user, order_data):
        order_data["supplier"] = "Supplier 5"

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "supplier" in serializer.errors
        assert serializer.errors["supplier"] == [
            (f"Supplier 'Supplier 5' does not exist. "
             "Please create a new supplier if this is a new entry.")
        ]

    def test_order_creation_fails_with_non_owned_supplier_name(self, user, order_data):
        # Create a different user and link it to a supplier
        user_2 = UserFactory.create(username="user_2")
        supplier = SupplierFactory.create(created_by=user_2)

        # Assign the order data to the supplier's name not owned by the context user
        order_data["supplier"] = supplier.name

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        assert "supplier" in serializer.errors
        assert serializer.errors["supplier"] == [
            (f"Supplier '{supplier.name}' does not exist. "
             "Please create a new supplier if this is a new entry.")
        ]

    def test_order_creation_fails_without_ordered_items(self, user, order_data):
        order_data.pop("ordered_items")

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert "This field is required." in serializer.errors["ordered_items"]

    def test_order_creation_fails_with_empty_ordered_items_list(self, user, order_data):
        order_data["ordered_items"] = []

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert "This field is required." in serializer.errors["ordered_items"]

    def test_order_creation_fails_with_empty_ordered_item_object(self, user, order_data):
        # Append empty object to the ordered_items list
        order_data["ordered_items"].append({})

        assert len(order_data["ordered_items"]) == 2

        serializer = SupplierOrderSerializer(
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

        # Add another ordered item with the same item name to the ordered_items list
        ordered_item_2 = {
            "item": ordered_item_1["item"],
            "ordered_quantity": 2,
            "ordered_price": 600
        }
        order_data["ordered_items"].append(ordered_item_2)

        assert len(order_data["ordered_items"]) == 2

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "ordered_items" in serializer.errors
        assert "item" in serializer.errors["ordered_items"]
        assert serializer.errors["ordered_items"]["item"] == (
            f"Item '{ordered_item_1['item']}' has been selected multiple times."
        )

    def test_order_creation_uses_supplier_ordered_item_serializer_for_ordered_items(
        self,
        user,
        supplier,
        ordered_item_data
    ):
        # Add second ordered item data object
        ordered_item_2_data = {
            "item": "Headphones",
            "supplier": supplier.name,
            "quantity": 5,
            "price": 620
        }

        # Define order data
        order_data = {
            "supplier": supplier.name,
            "ordered_items": [ordered_item_data, ordered_item_2_data]
        }

        # Mock the Supplier Ordered Item serializer to verify it's called
        ordered_item_serializer_path = "apps.supplier_orders.serializers.SupplierOrderedItemSerializer"
        with patch(ordered_item_serializer_path) as mock_ordered_item_serializer:
            # Mock instance of the Supplier Ordered Item serializer
            mock_ordered_item_instance = mock_ordered_item_serializer.return_value
            mock_ordered_item_instance.is_valid.return_value = True

            # Call the Supplier Order serializer
            serializer = SupplierOrderSerializer(
                data=order_data,
                context={"user": user}
            )
            assert serializer.is_valid(), serializer.errors

            order = serializer.save()
            assert str(order.created_by.id) == str(user.id)

            # Verify Supplier Ordered Item serializer was called twice
            assert mock_ordered_item_serializer.call_count == 2

            # Add order to the ordered items data for the data called with verification
            ordered_item_data["order"] = order.id
            ordered_item_2_data["order"] = order.id

            # Verify Supplier Ordered Item serializer was called with the correct data
            mock_ordered_item_serializer.assert_any_call(
                data=ordered_item_data,
                context={"user": user}
            )

            mock_ordered_item_serializer.assert_any_call(
                data=ordered_item_2_data,
                context={"user": user}
            )

            # Verify save method was called twice on the Supplier Ordered Item serializer
            assert mock_ordered_item_instance.save.call_count == 2

    def test_order_serializer_retrieves_delivery_and_payment_status_by_name(
        self,
        user,
        order_data,
        pending_status,
    ):
        order_data["payment_status"] = pending_status.name
        order_data["delivery_status"] = pending_status.name
        
        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert str(order.payment_status.id) == str(pending_status.id)
        assert str(order.delivery_status.id) == str(pending_status.id)

    def test_order_status_is_set_to_pending_by_default(self, user, order_data):
        # Remove delivery and payment status from order_data
        order_data.pop("delivery_status")
        order_data.pop("payment_status")

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        # Verify delivery and payment status have been set to Pending for order
        assert order.delivery_status is not None
        assert order.payment_status is not None
        assert order.delivery_status.name == "Pending"
        assert order.payment_status.name == "Pending"

    def test_order_creation_fails_with_invalid_delivery_status(self, user, order_data):
        invalid_status = "InvalidStatus"
        order_data["delivery_status"] = invalid_status

        # Verify that the status does not exist in the delivery status options
        assert invalid_status.lower() not in DELIVERY_STATUS_OPTIONS_LOWER

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        assert "delivery_status" in serializer.errors
        assert serializer.errors["delivery_status"] == ["Invalid delivery status."]

    def test_order_creation_fails_with_invalid_payment_status(self, user, order_data):
        invalid_status = "InvalidStatus"
        order_data["payment_status"] = invalid_status

        # Verify that the status does not exist in the payment status options
        assert invalid_status.lower() not in PAYMENT_STATUS_OPTIONS_LOWER

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        assert "payment_status" in serializer.errors
        assert serializer.errors["payment_status"] == ["Invalid payment status."]

    def test_delivered_order_ordered_items_in_inventory_state_update(
        self,
        user,
        supplier,
        order_data,
        delivered_status
    ):
        # Create two items in inventory and save a copy of their initial state
        item_1 = ItemFactory.create(
            created_by=user,
            supplier=supplier,
            name="Pack",
            in_inventory=True
        )
        initial_item_1 = copy.deepcopy(item_1)

        item_2 = ItemFactory.create(
            created_by=user,
            supplier=supplier,
            name="Projector",
            in_inventory=True
        )
        initial_item_2 = copy.deepcopy(item_2)

        # Define two ordered items for the order with the created inventory items
        ordered_item_1_data = {
            "item": item_1.name,
            "ordered_quantity": 2,
            "ordered_price": 500
        }
        ordered_item_2_data = {
            "item": item_2.name,
            "ordered_quantity": 2,
            "ordered_price": 600
        }
    
        # Add the two ordered items to the order data
        order_data["ordered_items"] = [ordered_item_1_data, ordered_item_2_data]

        # Define order delivery status as Delivered
        order_data["delivery_status"] = delivered_status.name

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.delivery_status.name == "Delivered"

        # Verify that the ordered items were created
        # and updated to the In Inventory state
        item_1.refresh_from_db()
        item_2.refresh_from_db()
        ordered_item_1 = SupplierOrderedItem.objects.get(order=order, item=item_1)
        ordered_item_2 = SupplierOrderedItem.objects.get(order=order, item=item_2)

        # Verify that the items and ordered items are linked correctly
        assert str(ordered_item_1.item.id) == str(item_1.id)
        assert str(ordered_item_2.item.id) == str(item_2.id)

        # Verify that the ordered quantity was added to the initial quantity
        assert item_1.quantity == ordered_item_1.ordered_quantity + initial_item_1.quantity
        assert item_2.quantity == ordered_item_2.ordered_quantity + initial_item_2.quantity

        # Verify that the average price was calculated correctly
        assert item_1.price == average_price(initial_item_1, ordered_item_1)
        assert item_2.price == average_price(initial_item_2, ordered_item_2)

    def test_delivered_order_new_ordered_items_in_inventory_state_create(
        self,
        user,
        order_data,
        delivered_status
    ):
        # Define two ordered items for the order
        ordered_item_1_data = {
            "item": "Pack",
            "ordered_quantity": 2,
            "ordered_price": 500
        }
        ordered_item_2_data = {
            "item": "Projector",
            "ordered_quantity": 2,
            "ordered_price": 600
        }
    
        # Verify that the items do not exist in inventory
        assert not Item.objects.filter(
            name__iexact=ordered_item_1_data["item"],
            in_inventory=True
        ).exists()

        assert not Item.objects.filter(
            name__iexact=ordered_item_2_data["item"],
            in_inventory=True
        ).exists()

        # Add the two ordered items to the order data
        order_data["ordered_items"] = [ordered_item_1_data, ordered_item_2_data]

        # Define order delivery status as Delivered
        order_data["delivery_status"] = delivered_status.name

        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )

        assert serializer.is_valid(), serializer.errors

        order = serializer.save()
        assert order.delivery_status.name == "Delivered"

        # Verify that the ordered items were created
        # and updated to the In Inventory state
        inventory_item_1 = Item.objects.get(
            name__iexact=ordered_item_1_data["item"],
            in_inventory=True
        )
        inventory_item_2 = Item.objects.get(
            name__iexact=ordered_item_2_data["item"],
            in_inventory=True
        )

        ordered_item_1 = SupplierOrderedItem.objects.get(
            order=order,
            item=inventory_item_1
        )
        ordered_item_2 = SupplierOrderedItem.objects.get(
            order=order,
            item=inventory_item_2
        )

        # Verify that the items and ordered items are linked correctly
        assert str(ordered_item_1.item.id) == str(inventory_item_1.id)
        assert str(ordered_item_2.item.id) == str(inventory_item_2.id)

        # Verify that the ordered quantity was set to item in inventory quantity
        assert inventory_item_1.quantity == ordered_item_1.ordered_quantity
        assert inventory_item_2.quantity == ordered_item_2.ordered_quantity

        # Verify that the ordered price was set to item in inventory price
        assert inventory_item_1.price == ordered_item_1.ordered_price
        assert inventory_item_2.price == ordered_item_2.ordered_price

    def test_order_creation_registers_a_new_activity(self, user, order_data):
        serializer = SupplierOrderSerializer(
            data=order_data,
            context={"user": user}
        )
        assert serializer.is_valid()

        order = serializer.save()

        assert Activity.objects.filter(
            action="created",
            model_name="supplier order",
            object_ref__contains=order.reference_id
        ).exists()

    def test_order_update(self, user, supplier_order, order_data, delivered_status):
        order_delivery_status = supplier_order.delivery_status
        order_tracking_number = supplier_order.tracking_number

        # Define order delivery status as Delivered and change tracking number
        order_data["delivery_status"] = delivered_status.name
        order_data["tracking_number"] = "ABC123"

        serializer = SupplierOrderSerializer(
            supplier_order,
            data=order_data,
            context={"user": user},
        )

        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify that the order delivery status and tracking number were updated
        assert str(order_update.delivery_status.id) == str(delivered_status.id)
        assert order_update.tracking_number == "ABC123"
        assert str(order_update.delivery_status.id) != str(order_delivery_status.id)
        assert order_update.tracking_number != order_tracking_number

    def test_order_partial_update(
        self,
        user,
        supplier_order,
        order_data,
        delivered_status
    ):
        order_delivery_status = supplier_order.delivery_status
        order_tracking_number = supplier_order.tracking_number

        # Define order delivery status as Delivered and change tracking number
        order_data["delivery_status"] = delivered_status.name
        order_data["tracking_number"] = "ABC123"

        serializer = SupplierOrderSerializer(
            supplier_order,
            data=order_data,
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify that the order delivery status and tracking number were updated
        assert str(order_update.delivery_status.id) == str(delivered_status.id)
        assert order_update.tracking_number == "ABC123"
        assert str(order_update.delivery_status.id) != str(order_delivery_status.id)
        assert order_update.tracking_number != order_tracking_number

    def test_supplier_update_fails_for_delivered_orders(
        self,
        user,
        supplier_order,
        delivered_status,
        ordered_item

    ):
        # Update order delivery status to Delivered
        supplier_order.delivery_status = delivered_status
        supplier_order.save()

        # Create a different supplier and assign it to the order's data
        supplier_2 = SupplierFactory.create(created_by=user, name="Supplier 2")
        order_data = {
            "supplier": supplier_2.name
        }

        serializer = SupplierOrderSerializer(
            supplier_order,
            data=order_data,
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid()

        # Verify that a ValidationError was raised
        # when we tried to save/update the order
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
        assert "supplier" in error_data["restricted_fields"]

    def test_ordered_items_update_fails_for_delivered_orders(
        self,
        user,
        supplier_order,
        delivered_status,
        ordered_item
    ):
        # Update order delivery status to Delivered
        supplier_order.delivery_status = delivered_status
        supplier_order.save()

        # Get order's data
        order_data = SupplierOrderSerializer(supplier_order).data

        # Remove 'total_price' and 'in_inventory' from ordered_items data
        keys_to_remove_from_items = ['total_price', 'in_inventory']
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

        serializer = SupplierOrderSerializer(
            supplier_order,
            data={'ordered_items': new_ordered_items},
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        # Verify that a ValidationError was raised
        # when we tried to save/update the order
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
        supplier_order,
        delivered_status,
        pending_status,
        ordered_item
    ):
        # Update order delivery status to Delivered
        supplier_order.delivery_status = delivered_status
        supplier_order.save()

        # Define order delivery status as Delivered
        order_data = {
            "delivery_status": pending_status.name
        }

        serializer = SupplierOrderSerializer(
            supplier_order,
            data=order_data,
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid()

        # Verify that a ValidationError was raised
        # when we tried to save/update the order
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

    def test_ordered_items_update_removes_missing_items(
        self,
        user,
        supplier_order,
    ):
        # Create two items for the order
        items = ItemFactory.create_batch(
            2,
            created_by=user,
            supplier=supplier_order.supplier,
        )
        for item in items:
            SupplierOrderedItemFactory.create(
                created_by=user,
                item=item,
                supplier=supplier_order.supplier,
                order=supplier_order
            )

        # Define new ordered items list
        new_items = ItemFactory.create_batch(
            2,
            created_by=user,
            supplier=supplier_order.supplier,
        )
        new_ordered_items = [
            {
                "item": item.name,
                "ordered_quantity": item.quantity - 1,
                "ordered_price": item.price + 100
            }
            for item in new_items
        ]

        # Call the SupplierOrderSerializer to update order's ordered_items
        serializer = SupplierOrderSerializer(
            supplier_order,
            data={"ordered_items": new_ordered_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify the length of the updated ordered_items list
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

        # Verify that the old items have been removed from the order ordered items
        assert all(str(item.id) not in updated_items_ids for item in items)

    def test_ordered_items_update_keeps_and_updated_existing_items(
        self,
        user,
        supplier_order,
    ):
        # Create two items for the order
        items = ItemFactory.create_batch(
            2, created_by=user, supplier=supplier_order.supplier
        )
        ordered_item_1 = SupplierOrderedItemFactory.create(
            created_by=user,
            item=items[0],
            supplier=supplier_order.supplier,
            order=supplier_order
        )
        ordered_item_2 = SupplierOrderedItemFactory.create(
            created_by=user,
            item=items[1],
            supplier=supplier_order.supplier,
            order=supplier_order
        )

        # Define new ordered items list
        new_items = ItemFactory.create_batch(
            2,
            created_by=user,
            supplier=supplier_order.supplier,
        )
        new_ordered_items = [
            {
                "item": item.name,
                "ordered_quantity": item.quantity - 1,
                "ordered_price": item.price + 100
            }
            for item in new_items
        ]

        # Add ordered_item_1 to the new ordered items list
        new_ordered_items.append(
            {
                "item": ordered_item_1.item.name,
                "ordered_quantity": ordered_item_1.ordered_quantity - 1,
                "ordered_price": ordered_item_1.ordered_price + 100
            }
        )

        # Call the SupplierOrderSerializer to update order's ordered_items
        serializer = SupplierOrderSerializer(
            supplier_order,
            data={"ordered_items": new_ordered_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        # Verify the length of the updated ordered_items list
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

        # Verify that ordered_item_1 remain in the order ordered items
        # and that its quantity and price have been updated
        existing_item = order_update.ordered_items.filter(
            item__id=ordered_item_1.item.id
        ).first()
        assert existing_item is not None
        assert str(existing_item.item.id) in updated_items_ids
        assert existing_item.ordered_quantity == ordered_item_1.ordered_quantity - 1
        assert existing_item.ordered_price == ordered_item_1.ordered_price + 100

        # Verify that ordered_item_2 has been removed from the order ordered items
        assert str(ordered_item_2.item.id) not in updated_items_ids
    
    def test_order_update_removes_optional_fields_if_set_to_none(
        self,
        user,
        supplier_order,
    ):
        assert supplier_order.tracking_number is not None
        assert supplier_order.shipping_cost is not None

        serializer = SupplierOrderSerializer(
            supplier_order,
            data={"tracking_number": None, "shipping_cost": None},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        assert order_update.tracking_number is None
        assert order_update.shipping_cost is None

        supplier_order.refresh_from_db()
        assert supplier_order.tracking_number is None
        assert supplier_order.shipping_cost is None

    def test_order_update_registers_a_new_activity(
        self,
        user,
        supplier_order,
    ):
        assert not Activity.objects.filter(
            action="updated",
            model_name="supplier order",
            object_ref__contains=supplier_order.reference_id
        ).exists()

        serializer = SupplierOrderSerializer(
            supplier_order,
            data={"tracking_number": "ABC123"},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        order_update = serializer.save()

        assert Activity.objects.filter(
            action="updated",
            model_name="supplier order",
            object_ref__contains=supplier_order.reference_id
        ).exists()

        assert order_update.tracking_number == "ABC123"

        supplier_order.refresh_from_db()
        assert supplier_order.tracking_number == "ABC123"

    def test_order_serializer_data_fields(self, user, supplier_order):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        expected_fields = {
            "id",
            "reference_id",
            "created_by",
            "supplier",
            "ordered_items",
            "total_quantity",
            "total_price",
            "delivery_status",
            "payment_status",
            "tracking_number",
            "shipping_cost",
            "created_at",
            "updated_at",
            "updated",
        }

        assert expected_fields.issubset(order_data.keys())

    def test_order_serializer_data_fields_types(self, supplier_order, ordered_item):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert isinstance(order_data["id"], str)
        assert isinstance(order_data["reference_id"], str)
        assert isinstance(order_data["created_by"], str)
        assert isinstance(order_data["supplier"], str)
        assert isinstance(order_data["ordered_items"], list)
        assert isinstance(order_data["total_quantity"], int)
        assert isinstance(order_data["total_price"], float)
        assert isinstance(order_data["delivery_status"], str)
        assert isinstance(order_data["payment_status"], str)
        assert isinstance(order_data["tracking_number"], str)
        assert isinstance(order_data["shipping_cost"], float)
        assert isinstance(order_data["created_at"], str)
        assert isinstance(order_data["updated_at"], str)
        assert isinstance(order_data["updated"], bool)

    def test_order_serializer_general_fields_data(self, supplier_order):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert order_data["id"] == str(supplier_order.id)
        assert order_data["reference_id"] == supplier_order.reference_id
        assert order_data["created_by"] == supplier_order.created_by.username
        assert order_data["supplier"] == supplier_order.supplier.name

    def test_order_serializer_ordered_items_data(self, supplier_order, ordered_item):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert len(order_data["ordered_items"]) == supplier_order.ordered_items.count()

        # Verify that ordered_item belongs to supplier_order
        assert str(supplier_order.id) == str(ordered_item.order.id)

        ordered_item_data = order_data["ordered_items"][0]

        assert str(ordered_item_data["id"]) == str(ordered_item.id)
        assert ordered_item_data["item"] == ordered_item.item.name
        assert ordered_item_data["ordered_quantity"] == ordered_item.ordered_quantity
        assert ordered_item_data["ordered_price"] == ordered_item.ordered_price
        assert ordered_item_data["total_price"] == ordered_item.total_price
        assert ordered_item_data["in_inventory"] == ordered_item.in_inventory

    def test_order_serializer_status_and_tracking_number_fields_data(self, supplier_order):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert order_data["delivery_status"] == supplier_order.delivery_status.name
        assert order_data["payment_status"] == supplier_order.payment_status.name
        assert order_data["tracking_number"] == supplier_order.tracking_number
    
    def test_order_serializer_date_fields_data(self, supplier_order):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert order_data["created_at"] == date_repr_format(supplier_order.created_at)
        assert order_data["updated_at"] == date_repr_format(supplier_order.updated_at)

    def test_order_serializer_financial_fields_data(self, supplier_order):
        serializer = SupplierOrderSerializer(supplier_order)
        order_data = serializer.data

        assert order_data["total_price"] == float(supplier_order.total_price)
        assert order_data["shipping_cost"] == float(supplier_order.shipping_cost)
