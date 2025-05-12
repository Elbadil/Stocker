import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from apps.sales.models import Sale, SoldItem
from apps.sales.factories import SaleFactory, SoldItemFactory


@pytest.mark.django_db
class TestSaleModel:
    """Tests for the sale model"""

    def test_sale_creation_with_related_objects(
        self,
        user,
        client,
        source,
        pending_status,
        location
    ):
        sale = SaleFactory.create(
            created_by=user,
            client=client,
            delivery_status=pending_status,
            payment_status=pending_status,
            shipping_address=location,
            source=source,
        )

        assert sale.created_by == user
        assert sale.client == client
        assert sale.delivery_status == pending_status
        assert sale.payment_status == pending_status
        assert sale.shipping_address == location
        assert sale.source == source

    def test_sale_str_representation(self):
        sale = SaleFactory.create()

        assert hasattr(sale, 'reference_id')
        assert str(sale) == sale.reference_id

    def test_sale_with_multiple_sold_items(self, sale):
        sold_items = SoldItemFactory.create_batch(3, sale=sale) 

        assert all(item.sale == sale for item in sold_items)
        assert sale.sold_items.count() == len(sold_items)


@pytest.mark.django_db
class TestSoldItemModel:
    """Tests for the sold item model"""

    def test_sold_item_creation_with_related_objects(self, user, sale, item):
        sold_item = SoldItemFactory.create(
            created_by=user,
            sale=sale,
            item=item
        )

        assert sold_item.created_by == user
        assert sold_item.sale == sale
        assert sold_item.item == item

    def test_sold_item_str_representation(self, user, sale, item):
        sold_item = SoldItemFactory.create(created_by=user, sale=sale, item=item)

        assert str(sold_item) == sold_item.item.name

    def test_sold_item_creation_fails_without_sale(self):
        with pytest.raises(IntegrityError):
            SoldItemFactory.create(sale=None)

    def test_sold_item_creation_fails_without_related_item(self):
        with pytest.raises(IntegrityError):
            SoldItemFactory.create(item=None)

    def test_sold_item_creation_fails_without_quantity(self):
        with pytest.raises(IntegrityError):
            SoldItemFactory.create(sold_quantity=None)

    def test_sold_item_creation_fails_without_price(self):
        with pytest.raises(IntegrityError):
            SoldItemFactory.create(sold_price=None)

    def test_sold_item_creation_fails_with_quantity_less_than_one(self):
        item = SoldItemFactory.create(sold_quantity=0)
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_sold_item_creation_fails_with_negative_price(self):
        item = SoldItemFactory.create(sold_price=-1)
        with pytest.raises(ValidationError):
            item.full_clean()
