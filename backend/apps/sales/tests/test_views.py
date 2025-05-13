import pytest
from django.urls import reverse
from apps.base.models import Activity
from apps.sales.models import Sale, SoldItem
from apps.sales.factories import SaleFactory, SoldItemFactory
from utils.serializers import decimal_to_float, date_repr_format


@pytest.fixture
def create_list_sales_url():
    return reverse('create_list_sales')

def sale_url(sale_id: str):
    return reverse('get_update_delete_sales', kwargs={'id': sale_id})


@pytest.mark.django_db
class TestCreateListSalesView:
    """Tests for the create list sales view"""

    def test_create_list_sales_view_requires_auth(self, api_client, create_list_sales_url):
        res = api_client.get(create_list_sales_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_sales_allowed_http_methods(
        self,
        auth_client,
        sale_data,
        create_list_sales_url
    ):
        get_res = auth_client.get(create_list_sales_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(create_list_sales_url, data=sale_data, format='json')
        assert post_res.status_code == 201

        put_res = auth_client.put(create_list_sales_url, data=sale_data, format='json')
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(create_list_sales_url, data=sale_data, format='json')
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(create_list_sales_url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_sale_creation_succeeds(self, auth_client, sale_data, create_list_sales_url):
        res = auth_client.post(create_list_sales_url, data=sale_data, format='json')
        assert res.status_code == 201

        res_data = res.json()
        assert "id" in res_data

        # Verify that Sale was created
        sale = Sale.objects.filter(id=res_data["id"]).first()
        assert isinstance(sale, Sale)

    def test_sale_created_by_authenticated_user(
        self,
        user,
        api_client,
        sale_data,
        create_list_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        res = api_client.post(
            create_list_sales_url,
            data=sale_data,
            format='json'
        )
        assert res.status_code == 201

        res_data = res.json()
        assert "created_by" in res_data
        assert res_data["created_by"] == user.username
        assert "id" in res_data

        # Verify that Sale was created with the authenticated user
        sale = Sale.objects.filter(id=res_data["id"]).first()
        assert isinstance(sale, Sale)
        assert str(sale.created_by.id) == str(user.id)

    def test_list_sales_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 6 sales for the authenticated user
        user_sales = SaleFactory.create_batch(6, created_by=user)

        # Create 5 sales for other users
        SaleFactory.create_batch(5)

        res = api_client.get(create_list_sales_url)
        assert res.status_code == 200

        res_data = res.json()
        assert len(res_data) == 6

        # Verify that all sales belong to the authenticated user
        assert all(sale["created_by"] == str(user.username)
                   for sale in res_data)

        user_sales_ids = {str(sale.id) for sale in user_sales}
        assert all(
            sale["id"] in user_sales_ids
            for sale in res_data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteSalesView:
    """Tests for the get update delete sales view"""

    def test_get_update_delete_sales_view_requires_auth(self, api_client, sale):
        url = sale_url(sale.id)

        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_sales_view_allowed_http_methods(
        self,
        auth_client,
        sale,
        sale_data
    ):
        url = sale_url(sale.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url, data=sale_data, format='json')
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url, data=sale_data, format='json')
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=sale_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_sale_operations_fail_with_inexistent_sale_id(self, auth_client, random_uuid):
        url = sale_url(random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test PATCH request
        patch_res = auth_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

    def test_sale_operations_fail_with_sale_not_linked_to_authenticated_user(
        self,
        user,
        api_client,
        sale,
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create a sale without linking it to the authenticated user
        sale = SaleFactory.create()
        url = sale_url(sale.id)

        # Test GET request
        get_res = api_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test PUT request
        put_res = api_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test PATCH request
        patch_res = api_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

        # Test DELETE request
        delete_res = api_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Sale matches the given query."

    def test_get_sale_with_valid_sale_id(
        self,
        user,
        api_client,
        sale
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        url = sale_url(sale.id)

        # Verify that the sale belongs to the authenticated user
        assert str(sale.created_by.id) == str(user.id)

        res = api_client.get(url)
        assert res.status_code == 200

    def test_sale_response_data_fields(self, auth_client, sale):
        url = sale_url(sale.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()
        
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

        assert expected_fields.issubset(res_data.keys())

    def test_sale_response_data_fields_types(self, auth_client, client_order, sale, sold_item):
        client_order.sale = sale
        client_order.save()

        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

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

    def test_sale_response_data_for_general_fields(self, auth_client, sale):
        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert sale_data["id"] == str(sale.id)
        assert sale_data["reference_id"] == sale.reference_id
        assert sale_data["created_by"] == sale.created_by.username
        assert sale_data["created_at"] == date_repr_format(sale.created_at)
        assert sale_data["updated_at"] == date_repr_format(sale.updated_at)
        assert sale_data["updated"] == sale.updated

    def test_sale_response_data_for_client_and_source_fields(self, auth_client, sale):
        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert sale_data["client"] == sale.client.name
        assert sale_data["source"] == sale.source.name

    def test_sale_response_sold_items_field_data(self, auth_client, sale, sold_item):
        assert str(sold_item.sale.id) == str(sale.id)

        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert len(sale_data["sold_items"]) == 1
        sold_item_data = sale_data["sold_items"][0]
        assert sold_item_data["item"] == sold_item.item.name
        assert sold_item_data["sold_quantity"] == sold_item.sold_quantity
        assert sold_item_data["sold_price"] == float(sold_item.sold_price)
        assert sold_item_data["total_price"] == float(sold_item.total_price)
        assert sold_item_data["total_profit"] == float(sold_item.total_profit)

    def test_sale_response_data_for_status_and_tracking_fields(self, auth_client, sale):
        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert sale_data["delivery_status"] == sale.delivery_status.name
        assert sale_data["payment_status"] == sale.payment_status.name
        assert sale_data["tracking_number"] == sale.tracking_number

    def test_sale_response_data_for_shipping_address_field(self, auth_client, sale):
        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        shipping_address = sale_data["shipping_address"]
        assert shipping_address["country"] == sale.shipping_address.country.name
        assert shipping_address["city"] == sale.shipping_address.city.name
        assert shipping_address["street_address"] == sale.shipping_address.street_address

    def test_sale_response_data_for_financial_fields(self, auth_client, sale):
        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert sale_data["shipping_cost"] == float(sale.shipping_cost)
        assert sale_data["net_profit"] == float(sale.net_profit)

    def test_sale_response_data_for_linked_order_field(self, auth_client, sale, client_order):
        client_order.sale = sale
        client_order.save()

        url = sale_url(sale.id)
        res = auth_client.get(url)
        assert res.status_code == 200
        sale_data = res.json()

        assert sale_data["linked_order"] is not None
        assert sale_data["linked_order"] == str(sale.order.id)

    def test_sale_put_update(self, auth_client, sale, sale_data, delivered_status):
        sale_data["delivery_status"] = delivered_status.name
        sale_data["tracking_number"] = "123456789"

        # Verify that sale's delivery status and tracking number are different
        # than the exiting ones
        sale.delivery_status.name != sale_data["delivery_status"] 
        sale.tracking_number != sale_data["tracking_number"]

        url = sale_url(sale.id)
        res = auth_client.put(url, data=sale_data, format='json')
        assert res.status_code == 200
        res_data = res.json()

        # Verify that sale delivery status and tracking number were updated
        assert res_data["delivery_status"] == sale_data["delivery_status"] 
        assert res_data["tracking_number"] == sale_data["tracking_number"]

        sale.refresh_from_db()
        assert sale.updated
        assert sale.delivery_status.name == delivered_status.name
        assert sale.tracking_number == "123456789"

    def test_sale_patch_update(self, auth_client, sale, delivered_status):
        sale_data = {
            "tracking_number": "123456789",
        }
        url = sale_url(sale.id)
        res = auth_client.patch(url, data=sale_data, format='json')
        assert res.status_code == 200
        res_data = res.json()

        # Verify that sale tracking number was updated
        assert res_data["tracking_number"] == sale_data["tracking_number"]
        sale.refresh_from_db()
        assert sale.updated
        assert sale.tracking_number == "123456789"

    def test_sale_deletion(self, auth_client, sale):
        url = sale_url(sale.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that sale record has been deleted
        assert not Sale.objects.filter(id=sale.id).exists()

    def test_sale_deletion_deletes_linked_sold_items(
        self,
        auth_client,
        sold_item,
        sale
    ):
        url = sale_url(sale.id)

        assert sold_item.sale.id == sale.id
        assert len(sale.sold_items.all()) > 0

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that sale record has been deleted
        assert not Sale.objects.filter(id=sale.id).exists()

        # Verify that linked sold item record has been deleted
        assert not SoldItem.objects.filter(
            sale__id=sale.id
        ).exists()

    def test_sale_deletion_resets_inventory_quantities_if_not_linked_to_an_order(
        self,
        auth_client,
        sold_item,
        sale
    ):
        item_in_inventory = sold_item.item
        item_quantity = item_in_inventory.quantity
        sold_quantity = sold_item.sold_quantity

        # Verify that sale is not linked to sale
        assert not sale.has_order

        url = sale_url(sale.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that sale record has been deleted
        assert not Sale.objects.filter(id=sale.id).exists()

        # Verify that linked sold item record has been deleted
        assert not SoldItem.objects.filter(
            sale__id=sale.id
        ).exists()

        # Verify that item's quantity has been reset
        item_in_inventory.refresh_from_db()
        assert item_in_inventory.quantity != item_quantity
        assert item_in_inventory.quantity == item_quantity + sold_quantity

    def test_sale_deletion_registers_a_new_activity(self, auth_client, sale):
        assert not Activity.objects.filter(
            action="deleted",
            model_name="sale",
            object_ref__contains=sale.reference_id
        ).exists()

        url = sale_url(sale.id)
        res = auth_client.delete(url)
        assert res.status_code == 204

        assert Activity.objects.filter(
            action="deleted",
            model_name="sale",
            object_ref__contains=sale.reference_id
        ).exists()


