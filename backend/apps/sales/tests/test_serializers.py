import pytest
from unittest.mock import patch
from rest_framework.exceptions import ValidationError
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.client_orders.models import Location, AcquisitionSource
from apps.client_orders.serializers import ClientOrderSerializer
from apps.client_orders.factories import AcquisitionSourceFactory, ClientFactory, LocationFactory, OrderStatusFactory
from apps.sales.models import Sale, SoldItem
from apps.sales.serializers import SaleSerializer, SoldItemSerializer
from apps.sales.factories import SoldItemFactory
from utils.status import (
    DELIVERY_STATUS_OPTIONS_LOWER,
    PAYMENT_STATUS_OPTIONS_LOWER
)
from utils.serializers import decimal_to_float, date_repr_format


@pytest.mark.django_db
class TestSoldItemSerializer:
    """Tests for the sold item serializer."""

    def test_sold_item_serializer_sets_created_by_from_context(self, user, sale, item):
        serializer = SoldItemSerializer(
            data={
                'item': item.name,
                'sale': sale.id,
                'sold_quantity': item.quantity - 1,
                'sold_price': item.price + 100
            },
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors
        item = serializer.save()
        assert item.created_by is not None
        assert str(item.created_by.id) == str(user.id)

    def test_sold_item_creation_with_valid_data(self, user, sold_item_data):
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        sold_item = serializer.save()
        assert str(sold_item.created_by.id) == str(user.id)
        assert str(sold_item.sale.id) == str(sold_item_data["sale"])
        assert sold_item.sold_quantity == sold_item_data["sold_quantity"]
        assert sold_item.sold_price == sold_item_data["sold_price"]

        assert isinstance(sold_item, SoldItem)
        assert SoldItem.objects.filter(id=sold_item.id).exists()

    def test_sold_item_creation_fails_without_sale(
        self,
        user,
        sold_item_data
    ):
        sold_item_data.pop("sale")
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "sale" in serializer.errors
        assert serializer.errors["sale"] == ["This field is required."]

    def test_sold_item_creation_fails_without_related_item(
        self,
        user,
        sold_item_data
    ):
        sold_item_data.pop("item")
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert serializer.errors["item"] == ["This field is required."]

    def test_sold_item_creation_fails_without_quantity(
        self,
        user,
        sold_item_data
    ):
        sold_item_data.pop("sold_quantity")
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "sold_quantity" in serializer.errors
        assert serializer.errors["sold_quantity"] == ["This field is required."]

    def test_sold_item_creation_fails_without_price(
        self,
        user,
        sold_item_data
    ):
        sold_item_data.pop("sold_price")
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "sold_price" in serializer.errors
        assert serializer.errors["sold_price"] == ["This field is required."]

    def test_sold_item_creation_fails_with_quantity_less_than_one(
        self,
        user,
        sold_item_data
    ):
        sold_item_data["sold_quantity"] = 0
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "sold_quantity" in serializer.errors
        assert serializer.errors["sold_quantity"] == [
            "Ensure this value is greater than or equal to 1."
        ]

    def test_sold_item_creation_fails_with_negative_price(
        self,
        user,
        sold_item_data
    ):
        sold_item_data["sold_price"] = -1
        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "sold_price" in serializer.errors
        assert serializer.errors["sold_price"] == [
            "Ensure this value is greater than or equal to 0.0."
        ]

    def test_sold_item_serializer_retrieves_related_item_by_name(
        self,
        user,
        item,
        sale
    ):
        serializer = SoldItemSerializer(
            data={
                'sale': sale.id,
                'item': item.name,
                'sold_quantity': item.quantity - 1,
                'sold_price': item.price + 100
            },
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors
        sold_item = serializer.save()
        assert str(sold_item.item.id) == str(item.id
)
    def test_sold_item_creation_fails_inexistent_item(
        self,
        user,
        sold_item_data
    ):
        random_item_name = "random_item_name"
        sold_item_data["item"] = random_item_name

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{random_item_name}' does not exist in your inventory."]
        )

    def test_sold_item_creation_fails_item_not_in_inventory(self, user, sold_item_data):
        item = ItemFactory.create(in_inventory=False)
        sold_item_data["item"] = item.name

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{item.name}' does not exist in your inventory."]
        )

    def test_sold_item_creation_fails_with_non_owned_item(self, user, sold_item_data):
        user_2 = UserFactory.create()
        item = ItemFactory.create(created_by=user_2)
        sold_item_data["item"] = item.name

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert not serializer.is_valid()

        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f"Item '{item.name}' does not exist in your inventory."]
        )

    def test_sold_item_creation_fails_for_delivered_sales(
        self,
        user,
        sale,
        item,
        delivered_status
    ):
        # Update sale delivery status to delivered
        sale.delivery_status = delivered_status
        sale.save()

        serializer = SoldItemSerializer(
            data={
                'sale': sale.id,
                'item': item.name,
                'sold_quantity': item.quantity - 1,
                'sold_price': item.price + 100
            },
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "sale" in errors.value.detail
        assert errors.value.detail["sale"] == (
            f"Cannot apply changes to the sale "
            f"with ID '{sale.id}' sold items "
            "because it has already been marked as Delivered. "
            "Changes to delivered sales are restricted "
            "to maintain data integrity."
        )

    def test_sold_item_creation_fails_with_existing_item_in_sale(
        self,
        user,
        sale,
        item,
        sold_item_data
    ):
        # Create a sold item for sale
        sold_item = SoldItemFactory.create(sale=sale, item=item)

        # Verify that the created sold item has the same name and sale id
        # of the sold_item_data's item and order
        assert sold_item_data["item"] == sold_item.item.name
        assert str(sold_item_data["sale"]) == str(sold_item.sale.id)

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "item" in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{sold_item_data['item']}' already exists in the sale's "
            "list of sold items. Consider updating the existing item "
            "if you need to modify its details."
        )

    def test_sold_quantity_exceeds_item_quantity_in_inventory(
        self,
        user,
        item,
        sold_item_data
    ):
        sold_quantity = 20
        sold_item_data["sold_quantity"] = sold_quantity
        sold_item_data["item"] = item.name

        # Verify that the sold quantity is greater than the item's quantity
        assert sold_quantity > item.quantity

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "sold_quantity" in errors.value.detail
        assert errors.value.detail["sold_quantity"] == (
            f"The sold quantity for '{item.name}' "
             "exceeds available stock."
        )

    def test_item_quantity_gets_reduced_by_sold_quantity(
        self,
        user,
        item,
        sold_item_data
    ):
        sold_quantity = item.quantity - 1
        sold_item_data["sold_quantity"] = sold_quantity
        sold_item_data["item"] = item.name
        item_initial_quantity = item.quantity

        serializer = SoldItemSerializer(
            data=sold_item_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        sold_item = serializer.save()

        # Ensure ordered quantity was set correctly
        assert sold_item.sold_quantity == sold_quantity

        # Ensure item quantity decreases by the correct amount
        item.refresh_from_db()
        assert item.quantity < item_initial_quantity
        assert item.quantity == item_initial_quantity - sold_quantity

    def test_sold_item_update(
        self,
        user,
        sold_item,
        sold_item_data
    ):
        initial_sold_quantity = sold_item.sold_quantity
        initial_sold_price = sold_item.sold_price

        sold_item_data["sold_quantity"] = initial_sold_quantity - 1
        sold_item_data["sold_price"] = initial_sold_price + 100

        serializer = SoldItemSerializer(
            sold_item,
            data=sold_item_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors
        item_update = serializer.save()

        assert item_update.sold_quantity == initial_sold_quantity - 1
        assert item_update.sold_price == initial_sold_price + 100

        item_update = SoldItem.objects.get(id=sold_item.id)
        assert item_update.sold_quantity == initial_sold_quantity - 1
        assert item_update.sold_price == initial_sold_price + 100

    def test_sold_item_partial_update(
        self,
        user,
        sold_item,
    ):
        initial_sold_price = sold_item.sold_price
        sold_item_data = {
            'sold_price': sold_item.sold_price + 100
        }

        serializer = SoldItemSerializer(
            sold_item,
            data=sold_item_data,
            context={'user': user},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        item_update = serializer.save()
        assert item_update.sold_price == initial_sold_price + 100

        item_update = SoldItem.objects.get(id=sold_item.id)
        assert item_update.sold_price == initial_sold_price + 100

    def test_sold_item_update_fails_for_delivered_sales(
        self,
        user,
        sale,
        sold_item,
        sold_item_data,
        delivered_status
    ):
        # Update sale delivery status to delivered
        sale.delivery_status = delivered_status
        sale.save()

        serializer = SoldItemSerializer(
            sold_item,
            data=sold_item_data,
            context={'user': user}
        )

        assert serializer.is_valid()

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "sale" in errors.value.detail
        assert errors.value.detail["sale"] == (
            f"Cannot apply changes to the sale "
            f"with ID '{sale.id}' sold items "
            "because it has already been marked as Delivered. "
            "Changes to delivered sales are restricted "
            "to maintain data integrity."
        )

    def test_sold_item_update_validates_item_uniqueness_if_changed(
        self,
        user,
        sale,
        sold_item,
    ):
        # Create an item and add it to the sale's sold items
        item_pack = ItemFactory.create(
            created_by=user,
            name="Pack",
            in_inventory=True
        )
        sold_item_pack = SoldItemFactory.create(
            created_by=user,
            sale=sale,
            item=item_pack
        )

        # Ensure both items belong to the same sale
        assert str(sold_item.sale.id) == str(sold_item_pack.sale.id)

        # Attempt to update the sold item's item with the same name as the existing item
        serializer = SoldItemSerializer(
            sold_item,
            data={"item": item_pack.name},
            context={"user": user},
            partial=True
        )

        assert serializer.is_valid(), serializer.errors

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "item" in errors.value.detail
        assert errors.value.detail["item"] == (
            f"Item '{item_pack.name}' already exists in the sale's "
            "list of sold items. Consider updating the existing item "
            "if you need to modify its details."
        )

    def test_sold_quantity_update_exceeds_item_in_inventory_quantity(
        self,
        user,
        item,
        sold_item,
    ):
        sold_quantity = sold_item.sold_quantity + 10
        sold_item_data = {
            'sold_quantity': sold_quantity
        }

        # Verify that the sold quantity is greater than the item's quantity
        assert str(sold_item.item.id) == str(item.id)
        assert sold_quantity > item.quantity

        serializer = SoldItemSerializer(
            sold_item,
            data=sold_item_data,
            context={'user': user},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "sold_quantity" in errors.value.detail
        assert errors.value.detail["sold_quantity"] == (
            f"The sold quantity for '{item.name}' "
            "exceeds available stock."
        )

    def test_sold_item_update_recalculates_item_in_inventory_quantity(
        self,
        user,
        item,
        sold_item,
    ):
        assert str(item.id) == str(sold_item.item.id)
   
        initial_item_quantity = item.quantity
        initial_sold_quantity = sold_item.sold_quantity
        new_sold_quantity = initial_sold_quantity - 2

        sold_item_data = {
            'sold_quantity': new_sold_quantity
        }

        serializer = SoldItemSerializer(
            sold_item,
            data=sold_item_data,
            context={'user': user},
            partial=True,
        )
        assert serializer.is_valid(), serializer.errors

        sold_item_update = serializer.save()
        assert sold_item_update.sold_quantity == new_sold_quantity

        # Ensure item in inventory gets back the sold quantity difference
        item.refresh_from_db()
        assert item.quantity > initial_item_quantity
        assert item.quantity == (
            initial_item_quantity + (initial_sold_quantity - new_sold_quantity)
        )

    def test_sold_item_serializer_data_fields(
        self,
        sold_item
    ):
        serializer = SoldItemSerializer(sold_item)
        item_data = serializer.data

        expected_fields = {
            'id',
            'created_by',
            'sale',
            'item',
            'sold_quantity',
            'sold_price',
            'total_price',
            'total_profit',
            'unit_profit',
            'created_at',
            'updated_at'
        }

        assert expected_fields.issubset(item_data.keys())

    def test_sold_item_serializer_data_fields_types(
        self,
        sold_item
    ):
        serializer = SoldItemSerializer(sold_item)
        item_data = serializer.data

        assert isinstance(item_data['id'], str)
        assert isinstance(item_data['created_by'], str)
        assert isinstance(item_data['sale'], str)
        assert isinstance(item_data['item'], str)
        assert isinstance(item_data['sold_quantity'], int)
        assert isinstance(item_data['sold_price'], float)
        assert isinstance(item_data['total_price'], float)
        assert isinstance(item_data['total_profit'], float)
        assert isinstance(item_data['unit_profit'], float)
        assert isinstance(item_data['created_at'], str)
        assert isinstance(item_data['updated_at'], str)

    def test_sold_item_serializer_data_fields_values(
        self,
        sold_item
    ):
        serializer = SoldItemSerializer(sold_item)
        item_data = serializer.data

        assert item_data['id'] == str(sold_item.id)
        assert item_data['created_by'] == sold_item.created_by.username
        assert item_data['sale'] == str(sold_item.sale.id)
        assert item_data['item'] == sold_item.item.name
        assert item_data['sold_quantity'] == sold_item.sold_quantity
        assert item_data['sold_price'] == decimal_to_float(sold_item.sold_price)
        assert item_data['total_price'] == decimal_to_float(sold_item.total_price)
        assert item_data['total_profit'] == decimal_to_float(sold_item.total_profit)
        assert item_data['unit_profit'] == decimal_to_float(sold_item.unit_profit)
        assert item_data['created_at'] == date_repr_format(sold_item.created_at)
        assert item_data['updated_at'] == date_repr_format(sold_item.updated_at)


@pytest.mark.django_db
class TestSaleSerializer:
    """Tests for the sale serializer."""

    def test_sale_serializer_sets_created_by_from_context(
        self,
        user,
        sale_data
    ):
        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert sale.created_by is not None
        assert str(sale.created_by.id) == str(user.id)

    def test_sale_creation_with_valid_data(
        self,
        user,
        client,
        location,
        source,
        pending_status,
        sale_data
    ):
        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert str(sale.created_by.id) == str(user.id)
        assert str(sale.client.id) == str(client.id)
        assert str(sale.shipping_address.id) == str(location.id)
        assert str(sale.delivery_status.id) == str(pending_status.id)
        assert str(sale.payment_status.id) == str(pending_status.id)
        assert str(sale.source.id) == str(source.id)

        assert isinstance(sale, Sale)
        assert Sale.objects.filter(id=sale.id).exists()

        # Verify that the sold item in sale's data was created
        assert isinstance(sale.sold_items.first(), SoldItem)
        sold_item = SoldItem.objects.filter(id=sale.sold_items.first().id).first()
        assert sold_item.item.name == sale_data["sold_items"][0]["item"]
        assert sold_item.sold_quantity == sale_data["sold_items"][0]["sold_quantity"]
        assert sold_item.sold_price == sale_data["sold_items"][0]["sold_price"]

    def test_sale_serializer_retrieves_client_by_name(
        self,
        user,
        client,
        sale_data
    ):
        assert client.name == sale_data["client"]

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert str(sale.client.id) == str(client.id)

    def test_sale_creation_fails_without_client(
        self,
        user,
        sale_data
    ):
        sale_data.pop("client")

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "client" in serializer.errors
        assert serializer.errors["client"] == ["This field is required."]

    def test_sale_creation_fails_without_inexistent_client(
        self,
        user,
        sale_data
    ):
        random_client_name = "RandomClient"
        sale_data["client"] = random_client_name

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        
        assert "client" in serializer.errors
        assert serializer.errors["client"] == [
            f"Client '{random_client_name}' does not exist. "
             "Please create a new client if this is a new entry."
        ]

    def test_sale_creation_fails_with_non_owned_client(
        self,
        user,
        sale_data
    ):
        user_2 = UserFactory.create()
        user_2_client = ClientFactory.create(created_by=user_2)

        sale_data["client"] = user_2_client.name

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "client" in serializer.errors
        assert serializer.errors["client"] == [
            f"Client '{user_2_client.name}' does not exist. "
             "Please create a new client if this is a new entry."
        ]

    def test_sale_creation_fails_without_sold_items(
        self,
        user,
        sale_data
    ):
        sale_data.pop("sold_items")

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "sold_items" in serializer.errors
        assert serializer.errors["sold_items"] == ["This field is required."]

    def test_sale_creation_fails_with_empty_sold_items_list(
        self,
        user,
        sale_data
    ):
        sale_data["sold_items"] = []

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "sold_items" in serializer.errors
        assert serializer.errors["sold_items"] == ["This field is required."]

    def test_sale_creation_fails_with_empty_sold_item_object(
        self,
        user,
        sale_data
    ):
        # Append an empty object to the sold_items list
        sale_data["sold_items"].append({})

        assert len(sale_data["sold_items"]) == 2

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "sold_items" in serializer.errors
        assert serializer.errors["sold_items"] == [
            f"Item at position 2 cannot be empty. Please provide valid details."
        ]

    def test_sale_creation_fails_with_duplicate_sold_item_object(
        self,
        user,
        sale_data
    ):
        sold_item_1 = sale_data["sold_items"][0]

        # Add a second sold item with the same item name to the sold_items list
        sold_item_2 = {
            "item": sold_item_1["item"],
            "sold_quantity": 2,
            "sold_price": 600
        }
        sale_data["sold_items"].append(sold_item_2)

        assert len(sale_data["sold_items"]) == 2

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()

        assert "sold_items" in serializer.errors
        assert "item" in serializer.errors["sold_items"]
        assert serializer.errors["sold_items"]["item"] == (
            f"Item '{sold_item_1['item']}' has been selected multiple times."
        )

    def test_sale_creation_uses_sold_item_serializer_for_sold_items(
        self,
        user,
        client,
        sold_item_data,
    ):
        # Add second sold item data object 
        item = ItemFactory.create(created_by=user, quantity=6, in_inventory=True)
        sold_item_2_data = {
            "item": item.name,
            "quantity": item.quantity - 2,
            "price": item.price + 100
        }

        # Define sale data
        sale_data = {
            "client": client.name,
            "sold_items": [sold_item_data, sold_item_2_data]
        }

        # Mock the Sold Item serializer to verify it's called
        sold_item_serializer_path = "apps.sales.serializers.SoldItemSerializer"
        with patch(sold_item_serializer_path) as mock_sold_item_serializer:
            # Mock instance of the Sold Item serializer
            mock_sold_item_instance = mock_sold_item_serializer.return_value
            mock_sold_item_instance.is_valid.return_value = True

            # Call the Sale serializer
            serializer = SaleSerializer(
                data=sale_data,
                context={'user': user}
            )
            assert serializer.is_valid(), serializer.errors

            sale = serializer.save()

            assert str(sale.client.id) == str(client.id)

            # Verify Sold Item serializer was called twice
            assert mock_sold_item_serializer.call_count == 2

            # Add sale to the sold items data for the data called with verification
            sold_item_data["sale"] = sale.id
            sold_item_2_data["sale"] = sale.id

            # Verify Sold Item serializer was called twice
            # with each sold item data
            mock_sold_item_serializer.assert_any_call(
                data=sold_item_data,
                context={"user": user}
            )

            mock_sold_item_serializer.assert_any_call(
                data=sold_item_2_data,
                context={"user": user}
            )

            # Verify save was called twice on the Sold Item serializer
            assert mock_sold_item_instance.save.call_count == 2

    def test_sale_creation_creates_new_shipping_address_if_not_exists(
        self,
        user,
        item,
        location_data,
        pending_status
    ):
        # Verify location does not exist before sale creation
        assert not Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).exists()

        # Define sale data with the inexistent location data
        client = ClientFactory.create(created_by=user)
        sale_data = {
            "client": client.name,
            "sold_items": [
                {
                    "item": item.name,
                    "sold_quantity": item.quantity - 2,
                    "sold_price": item.price + 100
                }
            ],
            "shipping_address": location_data,
            "delivery_status": pending_status.name,
            "payment_status": pending_status.name
        }

        serializer = SaleSerializer(
            data=sale_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert sale.shipping_address is not None

        # Verify location has been created and set to sale after sale creation
        location = Location.objects.filter(
            country__name__iexact=location_data["country"],
            city__name__iexact=location_data["city"],
            street_address__iexact=location_data["street_address"]
        ).first()
        assert location is not None
        assert str(sale.shipping_address.id) == str(location.id)

    def test_sale_creation_retrieves_existing_shipping_address(
        self,
        user,
        location,
        sale_data
    ):
        initial_location_count = Location.objects.count()

        # Set for sale's shipping_address the same existing location's data
        sale_data["shipping_address"] = {
            "country": location.country.name,
            "city": location.city.name,
            "street_address": location.street_address
        }

        serializer = SaleSerializer(
            data=sale_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert sale.shipping_address is not None

        # Verify the sale's shipping_address was set to 
        # the exact existing location
        assert str(sale.shipping_address.id) == str(location.id)

        # Verify no new location was created
        assert Location.objects.count() == initial_location_count

    def test_sale_creation_uses_location_serializer(
        self,
        user,
        client,
        sold_item_data,
        location_data
    ):
        sale_data = {
            "client": client.name,
            "sold_items": [sold_item_data],
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
            serializer = SaleSerializer(
                data=sale_data,
                context={'user': user}
            )
            assert serializer.is_valid()

            sale = serializer.save()

            assert str(sale.client.id) == str(client.id)

            # Verify location serializer was called with the correct data
            mock_location_serializer.assert_called_once_with(
                data=location_data,
                context={'user': user}
            )

            # Verify save was called on the location serializer
            mock_location_instance.save.assert_called_once()

            # Verify the created location was linked to the sale
            assert (
                sale.shipping_address ==
                mock_location_instance.save.return_value
            )
    
    def test_sale_creation_creates_new_source_if_not_exists(
        self,
        user,
        item,
        pending_status
    ):
        # Verify acq source does not exist before sale creation
        assert not AcquisitionSource.objects.filter(name__iexact="ADS").exists()

        # Define sale data with the inexistent source name
        client = ClientFactory.create(created_by=user)
        sale_data = {
            "client": client.name,
            "sold_items": [
                {
                    "item": item.name,
                    "sold_quantity": item.quantity - 2,
                    "sold_price": item.price + 100
                }
            ],
            "source": "ADS",
            "delivery_status": pending_status.name,
            "payment_status": pending_status.name
        }

        serializer = SaleSerializer(
            data=sale_data,
            context={'user': user}
        )
        assert serializer.is_valid()

        sale = serializer.save()
        assert sale.source is not None

        # Verify acq source has been created and set for sale after sale creation
        source = AcquisitionSource.objects.filter(name__iexact="ADS").first()
        assert source is not None
        assert str(sale.source.id) == str(source.id)

    def test_sale_serializer_retrieves_delivery_and_payment_status_by_name(
        self,
        user,
        pending_status,
        sale_data
    ):
        sale_data["delivery_status"] = pending_status.name
        sale_data["payment_status"] = pending_status.name

        serializer = SaleSerializer(
            data=sale_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert str(sale.delivery_status.id) == str(pending_status.id)
        assert str(sale.payment_status.id) == str(pending_status.id)

    def test_sale_status_is_set_to_pending_by_default(self, user, sale_data):
        # Remove delivery and payment status from sale_data
        sale_data.pop("delivery_status")
        sale_data.pop("payment_status")

        serializer = SaleSerializer(
            data=sale_data,
            context={'user': user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        # Verify delivery and payment status have been set to Pending for sale
        assert sale.delivery_status is not None
        assert sale.payment_status is not None
        assert sale.delivery_status.name == "Pending"
        assert sale.payment_status.name == "Pending"

    def test_sale_creation_fails_with_invalid_delivery_status(self, user, sale_data):
        invalid_status = "InvalidStatus"
        sale_data["delivery_status"] = invalid_status

        # Verify that the status does not exist in the delivery status options
        assert invalid_status.lower() not in DELIVERY_STATUS_OPTIONS_LOWER

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        assert "delivery_status" in serializer.errors
        assert serializer.errors["delivery_status"] == ["Invalid delivery status."]

    def test_sale_creation_fails_with_invalid_payment_status(self, user, sale_data):
        invalid_status = "InvalidStatus"
        sale_data["payment_status"] = invalid_status

        # Verify that the status does not exist in the payment status options
        assert invalid_status.lower() not in PAYMENT_STATUS_OPTIONS_LOWER

        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert not serializer.is_valid()
        assert "payment_status" in serializer.errors
        assert serializer.errors["payment_status"] == ["Invalid payment status."]

    def test_sale_creation_registers_a_new_activity(self, user, sale_data):
        serializer = SaleSerializer(
            data=sale_data,
            context={"user": user}
        )
        assert serializer.is_valid(), serializer.errors

        sale = serializer.save()
        assert Activity.objects.filter(
            user=user,
            action="created",
            model_name="sale",
            object_ref__contains=sale.reference_id
        ).exists()

    def test_sale_creation_from_delivered_client_order(
        self,
        user,
        client_order,
        delivered_status
    ):
        # Verify that the client order has no linked sale
        assert client_order.sale is None

        # Update client order's delivery status to delivered
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

        # Verify that the sale has been created with the order's data
        sale = order_update.sale
        assert str(sale.created_by.id) == str(order_update.created_by.id)
        assert str(sale.client.id) == str(order_update.client.id)
        assert str(sale.shipping_address.id) == str(order_update.shipping_address.id)
        assert str(sale.source.id) == str(order_update.source.id)
        assert str(sale.delivery_status.id) == str(order_update.delivery_status.id)
        assert str(sale.payment_status.id) == str(order_update.payment_status.id)
        assert len(sale.sold_items.all()) == len(order_update.ordered_items.all())

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
            in order_update.ordered_items.all()
        ]
        order_items_set = {frozenset(item.items()) for item in order_items}
        assert sale_items_set == order_items_set

    def test_sale_update(self, user, sale, sale_data):
        sale_delivery_status = sale.delivery_status
        sale_tracking_number = sale.tracking_number

        shipped_status = OrderStatusFactory.create(name="Shipped")
        sale_data["delivery_status"] = shipped_status.name
        sale_data["tracking_number"] = "ABCD123"

        serializer = SaleSerializer(
            sale,
            data=sale_data,
            context={"user": user}
        )
        assert serializer.is_valid()

        sale_update = serializer.save()
        assert sale_update.delivery_status != sale_delivery_status
        assert sale_update.tracking_number != sale_tracking_number

    def test_sale_partial_updated(self, user, sale):
        sale_tracking_number = sale.tracking_number
        sale_data = {
            "tracking_number": "ABCD123"
        }

        serializer = SaleSerializer(
            sale,
            data=sale_data,
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        sale_update = serializer.save()
        assert sale_update.tracking_number != sale_tracking_number
        assert sale_update.tracking_number == "ABCD123"

    def test_client_update_fails_for_delivered_sales(
        self,
        user,
        sale,
        delivered_status,
        sold_item
    ):
        # Update sale status to delivered
        sale.delivery_status = delivered_status
        sale.save()

        # Create a new client
        client = ClientFactory.create(created_by=user, name="Safuan")

        # Try to update sale with a new value for the client field
        serializer = SaleSerializer(
            sale,
            data={"client": client.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        # Verify a ValidationError is raised when we try to save/update the sale
        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This sale and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "client" in error_data["restricted_fields"]

    def test_sold_items_update_fails_for_delivered_sales(
        self,
        user,
        sale,
        delivered_status,
        sold_item
    ):
        # Update sale status to delivered
        sale.delivery_status = delivered_status
        sale.save()

        # Get sale's data
        sale_data = SaleSerializer(sale).data

        # Remove 'total_price' and 'total_profit' from sold_items data
        keys_to_remove_from_items = ['total_price', 'total_profit']
        sold_items = []
        for item in sale_data["sold_items"]:
            sold_items.append(
                {key: value for key,
                 value in item.items()
                 if key not in keys_to_remove_from_items}
            )
        sold_items_set = {frozenset(item.items()) for item in sold_items}

        # Define new sold items
        new_sold_items = [
            {
                "item": "DataShow",
                "sold_quantity": 4,
                "sold_price": 500
            }
        ]
        new_sold_items_set = {
            frozenset(item.items())
            for item in new_sold_items
        }

        # Verify that new sold items are different than sale's sold items
        assert new_sold_items_set != sold_items_set

        # Try to update sale with new sold items
        serializer = SaleSerializer(
            sale,
            data={"sold_items": new_sold_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        # Verify a ValidationError is raised when we try to save/update the sale
        with pytest.raises(ValidationError) as errors:
            serializer.save()
    
        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This sale and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "sold_items" in error_data["restricted_fields"]

    def test_delivery_status_update_fails_for_delivered_sales(
        self,
        user,
        sale,
        pending_status,
        delivered_status,
        sold_item
    ):
        # Update sale status to delivered
        sale.delivery_status = delivered_status
        sale.save()

        # Try to update sale with a new value for the delivery_status field
        serializer = SaleSerializer(
            sale,
            data={"delivery_status": pending_status.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        # Verify a ValidationError is raised when we try to save/update the sale
        with pytest.raises(ValidationError) as errors:
            serializer.save()

        assert "error" in errors.value.detail
        error_data = errors.value.detail["error"]

        assert "message" in error_data
        assert error_data["message"] == (
            'This sale and has already been marked as delivered. '
            'Restricted fields cannot be modified.'
        )

        assert "restricted_fields" in error_data
        assert "delivery_status" in error_data["restricted_fields"]

    def test_sold_items_update_removes_missing_items(self, user, sale):
        # Create two items for the sale
        items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        for item in items:
            SoldItemFactory.create(
                created_by=user,
                item=item,
                sale=sale
            )

        # Define new sold items list
        new_items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        new_sold_items = [
            {
                "item": item.name,
                "sold_quantity": item.quantity - 1,
                "sold_price": item.price + 100
            }
            for item in new_items
        ]

        # Call the SaleSerializer to update sale's sold_items
        serializer = SaleSerializer(
            sale,
            data={"sold_items": new_sold_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        sale_update = serializer.save()

        # Verify the length of the sale's new sold_items
        sold_items_update = sale_update.sold_items.all()
        assert sold_items_update.count() == 2
        assert len(sold_items_update) == len(new_sold_items)

        updated_items_ids = [
            str(sold_item.item.id)
            for sold_item
            in sold_items_update
        ]

        # Verify that the new items have been added to the sale sold items
        assert all(str(item.id) in updated_items_ids for item in new_items)

        # Verify that the old items have been excluded from the sale's
        # sold items list
        assert all(str(item.id) not in updated_items_ids for item in items)

    def test_sold_items_update_keeps_and_updates_existing_items(
        self,
        user,
        sale
    ):
        # Create two items for the sale
        items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        sold_item_1 = SoldItemFactory.create(
            created_by=user,
            sale=sale,
            item=items[0]
        )
        sold_item_2 = SoldItemFactory.create(
            created_by=user,
            sale=sale,
            item=items[1]
        )

        # Define new sold items list
        new_items = ItemFactory.create_batch(2, created_by=user, in_inventory=True)
        new_sold_items = [
            {
                "item": item.name,
                "sold_quantity": item.quantity - 1,
                "sold_price": item.price + 100
            }
            for item in new_items
        ]

        # Add sold_item_1 to the new sold items list
        # with different sold_quantity and sold_price
        new_sold_items.append({
            "item": sold_item_1.item.name,
            "sold_quantity": sold_item_1.sold_quantity - 1,
            "sold_price": sold_item_1.sold_price + 100,
        })

        # Call the SaleSerializer to update sale's sold_items
        serializer = SaleSerializer(
            sale,
            data={"sold_items": new_sold_items},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        sale_update = serializer.save()

        # Verify the length of the sale's new sold_items
        sold_items_update = sale_update.sold_items.all()
        assert sold_items_update.count() == 3
        assert len(sold_items_update) == len(new_sold_items)

        updated_items_ids = [
            str(sold_item.item.id)
            for sold_item
            in sold_items_update
        ]

        # Verify that the new items have been added to the sale sold items
        assert all(str(item.id) in updated_items_ids for item in new_items)

        # Verify that sold_item_1 remained in the sale's sold items list
        # and that its quantity and price got updated
        existing_item = sale_update.sold_items.filter(
            item__id=sold_item_1.item.id
        ).first()
        assert existing_item is not None
        assert str(existing_item.item.id) in updated_items_ids
        assert existing_item.sold_quantity == sold_item_1.sold_quantity - 1
        assert existing_item.sold_price == sold_item_1.sold_price + 100

        # Verify that sold_item_2 has been excluded from
        # the sale's sold items list
        assert str(sold_item_2.item.id) not in updated_items_ids

    def test_sale_update_removes_optional_field_if_set_to_none(
        self,
        user,
        sale,
    ):
        assert sale.shipping_address is not None
        assert sale.source is not None

        serializer = SaleSerializer(
            sale,
            data={
                "shipping_address": None,
                "source": None, 
            },
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        sale_update = serializer.save()
        assert sale_update.updated
        assert sale.shipping_address is None
        assert sale.source is None

    def test_client_order_status_update_to_delivered_creates_a_sale_with_orders_data(
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
            in order_update.ordered_items.all()
        ]
        order_items_set = {frozenset(item.items()) for item in order_items}
        assert sale_items_set == order_items_set

    def test_changes_to_sale_reflect_to_linked_order(
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

        # Update sale's source of acquisition
        emailing_source = AcquisitionSourceFactory.create(
            added_by=user,
            name="Emailing"
        )
        serializer = SaleSerializer(
            sale,
            data={"source": emailing_source.name},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        sale_update = serializer.save()
        linked_order = sale_update.order

        # Verify that source has been updated for both sale and order
        assert str(sale_update.source.id) == str(emailing_source.id)
        assert str(sale_update.source.id) == str(linked_order.source.id)

    def test_sale_update_registers_a_new_activity(
        self,
        user,
        sale,
    ):
        serializer = SaleSerializer(
            sale,
            data={
                "shipping_address": None,
                "source": None, 
            },
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

        sale_update = serializer.save()
        assert sale_update.updated

        assert Activity.objects.filter(
            user=user,
            action="updated",
            model_name="sale",
            object_ref__contains=sale.reference_id
        ).exists()

    def test_sale_serializer_data_fields(self, sale):
        serializer = SaleSerializer(sale)

        expected_fields = {
            'id',
            'reference_id',
            'created_by',
            'client',
            'sold_items',
            'delivery_status',
            'payment_status',
            'source',
            'shipping_address',
            'shipping_cost',
            'tracking_number',
            'net_profit',
            'linked_order',
            'created_at',
            'updated_at',
            'updated',
        }

        assert expected_fields.issubset(serializer.data.keys())
    
    def test_sale_serializer_data_fields_types(self, client_order, sale, sold_item):
        client_order.sale = sale
        client_order.save()

        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert isinstance(sale_data["id"], str)
        assert isinstance(sale_data["reference_id"], str)
        assert isinstance(sale_data["created_by"], str)
        assert isinstance(sale_data["client"], str)
        assert isinstance(sale_data["sold_items"], list)
        assert isinstance(sale_data["delivery_status"], str)
        assert isinstance(sale_data["payment_status"], str)
        assert isinstance(sale_data["source"], str)
        assert isinstance(sale_data["shipping_address"], dict)
        assert isinstance(sale_data["shipping_cost"], float)
        assert isinstance(sale_data["tracking_number"], str)
        assert isinstance(sale_data["net_profit"], float)
        assert isinstance(sale_data["linked_order"], str)
        assert isinstance(sale_data["created_at"], str)
        assert isinstance(sale_data["updated_at"], str)
        assert isinstance(sale_data["updated"], bool)

    def test_sale_serializer_general_fields_data(self, sale):
        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert sale_data["id"] == str(sale.id)
        assert sale_data["reference_id"] == sale.reference_id
        assert sale_data["created_by"] == sale.created_by.username
        assert sale_data["created_at"] == date_repr_format(sale.created_at)
        assert sale_data["updated_at"] == date_repr_format(sale.updated_at)
        assert sale_data["updated"] == sale.updated

    def test_sale_serializer_client_and_source_fields_data(self, sale):
        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert sale_data["client"] == sale.client.name
        assert sale_data["source"] == sale.source.name

    def test_sale_serializer_sold_items_field_data(self, sale, sold_item):
        assert str(sold_item.sale.id) == str(sale.id)

        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert len(sale_data["sold_items"]) == 1
        sold_item_data = sale_data["sold_items"][0]
        assert sold_item_data["item"] == sold_item.item.name
        assert sold_item_data["sold_quantity"] == sold_item.sold_quantity
        assert sold_item_data["sold_price"] == sold_item.sold_price
        assert sold_item_data["total_price"] == sold_item.total_price
        assert sold_item_data["total_profit"] == sold_item.total_profit

    def test_sale_serializer_status_and_tracking_fields_data(self, sale):
        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert sale_data["delivery_status"] == sale.delivery_status.name
        assert sale_data["payment_status"] == sale.payment_status.name
        assert sale_data["tracking_number"] == sale.tracking_number

    def test_sale_serializer_shipping_address_field_data(self, sale):
        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        shipping_address = sale_data["shipping_address"]
        assert shipping_address["country"] == sale.shipping_address.country.name
        assert shipping_address["city"] == sale.shipping_address.city.name
        assert shipping_address["street_address"] == sale.shipping_address.street_address

    def test_sale_serializer_financial_fields_data(self, sale):
        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert sale_data["shipping_cost"] == float(sale.shipping_cost)
        assert sale_data["net_profit"] == float(sale.net_profit)

    def test_sale_serializer_linked_order_field_data(self, sale, client_order):
        client_order.sale = sale
        client_order.save()

        serializer = SaleSerializer(sale)
        sale_data = serializer.data

        assert sale_data["linked_order"] is not None
        assert sale_data["linked_order"] == str(sale.order.id)
        assert sale_data["linked_order"] == str(client_order.id)
