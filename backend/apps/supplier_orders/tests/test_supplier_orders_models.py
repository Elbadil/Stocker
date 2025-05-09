import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from apps.supplier_orders.models import (
    Supplier,
    SupplierOrder,
    SupplierOrderedItem
)
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderFactory,
    SupplierOrderedItemFactory
)


@pytest.mark.django_db
class TestSupplierModel:
    """Tests for Supplier model"""

    def test_supplier_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            Supplier.objects.create(name=None)

    def test_supplier_creation_fails_with_blank_name(self):
        supplier = SupplierFactory.create(name="")
        with pytest.raises(ValidationError):
            supplier.full_clean()

    def test_supplier_creation_fails_with_existing_name(self):
        SupplierFactory.create(name="supplier")
        with pytest.raises(IntegrityError):
            SupplierFactory.create(name="supplier")

    def test_supplier_creation_succeeds(self):
        SupplierFactory.create(name="supplier")
        assert Supplier.objects.filter(name="supplier").exists()

    def test_supplier_creation_with_related_objects(self, user, location):
        supplier = SupplierFactory.create(
            created_by=user,
            location=location
        )
        assert str(supplier.created_by.id) == str(user.id)
        assert str(supplier.location.id) == str(location.id)

    def test_supplier_str_representation(self):
        supplier = SupplierFactory.create(name="supplier")
        assert str(supplier) == "supplier"
        assert str(supplier) == supplier.name

    def test_supplier_with_multiple_orders(self):
        supplier = SupplierFactory.create(name="supplier")
        orders = SupplierOrderFactory.create_batch(2, supplier=supplier)

        assert supplier.total_orders == 2
        assert all(order.supplier == supplier for order in orders)


@pytest.mark.django_db
class TestSupplierOrderModel:
    """Tests for SupplierOrder model"""

    def test_supplier_order_creation_with_related_objects(
        self,
        user,
        supplier,
        pending_status
    ):
        supplier_order = SupplierOrderFactory.create(
            created_by=user,
            supplier=supplier,
            delivery_status=pending_status,
            payment_status=pending_status,
        )

        assert str(supplier_order.created_by.id) == str(user.id)
        assert str(supplier_order.supplier.id) == str(supplier.id)
        assert str(supplier_order.delivery_status.id) == str(pending_status.id)
        assert str(supplier_order.payment_status.id) == str(pending_status.id)

    def test_supplier_order_str_representation(self):
        supplier_order = SupplierOrderFactory.create()
        assert hasattr(supplier_order, "reference_id")
        assert supplier_order.reference_id is not None
        assert str(supplier_order) == supplier_order.reference_id

    def test_supplier_order_with_multiple_items(self):
        supplier_order = SupplierOrderFactory.create()
        items = SupplierOrderedItemFactory.create_batch(
            2,
            order=supplier_order
        )

        assert supplier_order.items.count() == 2
        assert all(item.order == supplier_order for item in items)


@pytest.mark.django_db
class TestSupplierOrderedItemModel:
    """Tests for SupplierOrderedItem model"""

    def test_ordered_item_creation_with_related_objects(
        self,
        user,
        supplier,
        supplier_order,
        item,
    ):
        ordered_item = SupplierOrderedItemFactory.create(
            created_by=user,
            order=supplier_order,
            supplier=supplier,
            item=item,
            ordered_quantity=item.quantity - 1,
            ordered_price=item.price,
        )

        assert str(ordered_item.created_by.id) == str(user.id)
        assert str(ordered_item.order.id) == str(supplier_order.id)
        assert str(ordered_item.supplier.id) == str(supplier.id)
        assert str(ordered_item.item.id) == str(item.id)

    def test_ordered_item_str_representation(
        self,
        user,
        supplier,
        supplier_order,
        item
    ):
        ordered_item = SupplierOrderedItemFactory.create(
            created_by=user,
            supplier=supplier,
            order=supplier_order,
            item=item,
            ordered_quantity=4
        )

        assert str(ordered_item) == item.name

    def test_ordered_item_creation_fails_without_quantity(self):
        with pytest.raises(IntegrityError):
            SupplierOrderedItemFactory.create(ordered_quantity=None)

    def test_ordered_item_creation_fails_without_price(self):
        with pytest.raises(IntegrityError):
            SupplierOrderedItemFactory.create(ordered_price=None)

    def test_ordered_item_creation_fails_with_quantity_less_than_one(self):
        ordered_item = SupplierOrderedItemFactory.create(ordered_quantity=0)
        with pytest.raises(ValidationError):
            ordered_item.full_clean()

    def test_ordered_item_creation_fails_with_negative_price(self):
        ordered_item = SupplierOrderedItemFactory.create(ordered_price=-1)
        with pytest.raises(ValidationError):
            ordered_item.full_clean()
