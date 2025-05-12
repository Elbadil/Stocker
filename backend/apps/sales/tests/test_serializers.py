import pytest
from rest_framework.exceptions import ValidationError
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.sales.models import Sale, SoldItem
from apps.sales.serializers import SaleSerializer, SoldItemSerializer
from apps.sales.factories import SaleFactory, SoldItemFactory


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


