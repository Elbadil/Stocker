import pytest
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


