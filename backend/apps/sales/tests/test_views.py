import pytest
import uuid
from typing import Union
from django.urls import reverse
from apps.base.models import Activity
from apps.inventory.factories import ItemFactory
from apps.sales.models import Sale, SoldItem
from apps.sales.factories import SaleFactory, SoldItemFactory
from utils.serializers import decimal_to_float, date_repr_format


@pytest.fixture
def create_list_sales_url():
    return reverse('create_list_sales')

def sale_url(sale_id: str):
    return reverse('get_update_delete_sales', kwargs={'id': sale_id})

@pytest.fixture
def bulk_delete_sales_url():
    return reverse('bulk_delete_sales')

def sold_item_url(sale_id: str, item_id: Union[str, None]=None):
    if item_id:
        return reverse('get_update_delete_sold_items',
                       kwargs={'sale_id': sale_id, 'id': item_id})
    return reverse('create_list_sold_items', kwargs={'sale_id': sale_id})

def bulk_delete_items_url(sale_id: str):
    return reverse('bulk_delete_sold_items', kwargs={'sale_id': sale_id})


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


@pytest.mark.django_db
class TestBulkDeleteSalesView:
    """Tests for the bulk delete sales view."""

    def test_bulk_delete_sales_view_requires_auth(self, api_client, bulk_delete_sales_url):
        res = api_client.delete(bulk_delete_sales_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_sales_view_allowed_http_methods(
        self,
        auth_client,
        sale,
        bulk_delete_sales_url
    ):
        get_res = auth_client.get(bulk_delete_sales_url)
        assert get_res.status_code == 405
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "Method \"GET\" not allowed."

        post_res = auth_client.post(bulk_delete_sales_url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(bulk_delete_sales_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(bulk_delete_sales_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id]},
            format='json'
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_sales_fails_without_ids_list(
        self,
        auth_client,
        bulk_delete_sales_url
    ):
        res = auth_client.delete(bulk_delete_sales_url)
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_sales_fails_with_empty_ids_list(
        self,
        auth_client,
        bulk_delete_sales_url
    ):
        res = auth_client.delete(bulk_delete_sales_url, data={"ids": []}, format='json')
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_sales_fails_with_invalid_uuids(
        self,
        auth_client,
        sale,
        bulk_delete_sales_url
    ):
        res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id, "invalid_uuid_1", "invalid_uuid_2"]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid UUIDs."

        assert "invalid_uuids" in res_error
        assert len(res_error["invalid_uuids"]) == 2
        assert "invalid_uuid_1" in res_error["invalid_uuids"]
        assert "invalid_uuid_2" in res_error["invalid_uuids"]

    def test_bulk_delete_sales_fails_with_nonexistent_ids(
        self,
        auth_client,
        sale,
        bulk_delete_sales_url
    ):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())

        res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id, random_id_1, random_id_2]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all selected sales are not found."

        assert "missing_ids" in res_error
        assert len(res_error["missing_ids"]) == 2
        assert random_id_1 in res_error["missing_ids"]
        assert random_id_2 in res_error["missing_ids"]

    def test_bulk_delete_sales_fails_with_unauthorized_sales(
        self,
        user,
        api_client,
        bulk_delete_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user)

        user_sales = SaleFactory.create_batch(2, created_by=user)
        other_sales = SaleFactory.create_batch(3)

        sales = user_sales + other_sales
        sales_ids = [sale.id for sale in sales]

        res = api_client.delete(
            bulk_delete_sales_url,
            data={"ids": sales_ids},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all selected sales are not found."

        assert "missing_ids" in res_error
        assert len(res_error["missing_ids"]) == len(other_sales)
        assert all(str(sale.id) in res_error["missing_ids"] for sale in other_sales)

    def test_bulk_delete_sales_with_valid_sales(
        self,
        user,
        api_client,
        sale,
        bulk_delete_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user)

        # Create another sale for the authenticated user
        user_sale = SaleFactory.create(created_by=user)

        # Verify that both sales belong to the authenticated user
        assert str(sale.created_by.id) == str(user.id)
        assert str(user_sale.created_by.id) == str(user.id)

        sales = [sale, user_sale]
        sales_ids = [sale.id for sale in sales]

        res = api_client.delete(
            bulk_delete_sales_url,
            data={"ids": sales_ids},
            format='json'
        )
        assert res.status_code == 200

        # Verify that both sales were deleted
        assert not Sale.objects.filter(id__in=sales_ids).exists()

    def test_bulk_delete_sales_deletes_linked_sold_items(
        self,
        user,
        auth_client,
        sale,
        sold_item,
        bulk_delete_sales_url
    ):
        # Verify that the sold item is linked to the sale
        assert str(sold_item.sale.id) == str(sale.id)

        # Create another sale with another sold_item
        item_2 = ItemFactory.create(created_by=user, in_inventory=True)
        sale_2 = SaleFactory.create(created_by=user)
        sold_item_2 = SoldItemFactory.create(
            created_by=user,
            sale=sale_2,
            item=item_2,
            sold_quantity=item_2.quantity - 1
        )

        res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id, sale_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 sales successfully deleted."

        # Verify that the two sales have been deleted
        assert not Sale.objects.filter(
            id__in=[sale.id, sale_2.id]
        ).exists()

        # Verify that linked sold items have been deleted
        assert not SoldItem.objects.filter(
            sale__id__in=[sale.id, sale_2.id]
        ).exists()

    def test_bulk_delete_sales_resets_inventory_quantities_if_not_linked_to_sales(
        self,
        user,
        auth_client,
        sale,
        sold_item,
        bulk_delete_sales_url
    ):
        # Verify that the sold item is linked to the sale
        assert str(sold_item.sale.id) == str(sale.id)

        item_1 = sold_item.item
        item_1_quantity = item_1.quantity
 
        # Create another sale with another sold_item
        item_2 = ItemFactory.create(created_by=user, in_inventory=True)
        item_2_quantity = item_2.quantity
        sale_2 = SaleFactory.create(created_by=user)
        sold_item_2 = SoldItemFactory.create(
            created_by=user,
            sale=sale_2,
            item=item_2,
            sold_quantity=item_2_quantity - 1
        )

        # Verify that the sales are not linked to orders
        assert not sale.has_order
        assert not sale_2.has_order

        res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id, sale_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 sales successfully deleted."

        # Verify that the two sales have been deleted
        assert not Sale.objects.filter(
            id__in=[sale.id, sale_2.id]
        ).exists()

        # Verify that the linked sold items have been deleted
        assert not SoldItem.objects.filter(
            sale__id__in=[sale.id, sale_2.id]
        ).exists()

        # Verify that the sold items's inventory quantity has been reset
        item_1.refresh_from_db()
        assert item_1.quantity != item_1_quantity
        assert item_1.quantity == item_1_quantity + sold_item.sold_quantity

        item_2.refresh_from_db()
        assert item_2.quantity != item_2_quantity
        assert item_2.quantity == item_2_quantity + sold_item_2.sold_quantity

    def test_bulk_delete_sales_registers_a_new_activity(
        self,
        user,
        auth_client,
        sale,
        bulk_delete_sales_url
    ):
        # Create another sale
        sale_2 = SaleFactory.create(created_by=user)

        res = auth_client.delete(
            bulk_delete_sales_url,
            data={"ids": [sale.id, sale_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 sales successfully deleted."

        # Verify that the two sales have been deleted
        assert not Sale.objects.filter(
            id__in=[sale.id, sale_2.id]
        ).exists()

        # Verify that a new activity has been created
        assert Activity.objects.filter(
            user=user,
            action="deleted",
            model_name="sale",
            object_ref__contains=[
                sale.reference_id,
                sale_2.reference_id
            ]
        ).exists()


@pytest.mark.django_db
class TestCreateListSoldItemsView:
    """Tests for the create list sold items view"""

    def test_create_list_sold_items_view_requires_auth(self, api_client, sale):
        url = sold_item_url(sale.id)

        res = api_client.get(url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_sold_items_view_allowed_http_methods(
        self,
        auth_client,
        sold_item_data,
        sale
    ):
        url = sold_item_url(sale.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url, data=sold_item_data, format='json')
        assert post_res.status_code == 201

        put_res = auth_client.put(url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_create_list_sold_items_fails_with_nonexistent_sale_id(
        self,
        auth_client,
        sold_item_data,
        random_uuid,
    ):
        url = sold_item_url(random_uuid)

        res = auth_client.post(url, data=sold_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Sale with id '{random_uuid}' does not exist."

    def test_create_list_sold_items_fails_with_unauthorized_sale(
        self,
        api_client,
        user,
        sold_item_data,
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create an sale with a different user
        sale = SaleFactory.create()

        # Verify the created sale is not linked to the authenticated user
        assert str(sale.created_by.id) != str(user.id)

        url = sold_item_url(sale.id)

        res = api_client.post(url, data=sold_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Sale with id '{sale.id}' does not exist."

    def test_create_sold_item_with_valid_sale_id_and_data(
        self,
        auth_client,
        sold_item_data,
        sale
    ):
        url = sold_item_url(sale.id)

        res = auth_client.post(url, data=sold_item_data, format='json')
        assert res.status_code == 201

        # Verify that the sold item has been created
        assert "id" in res.data
        sold_item = SoldItem.objects.filter(id=res.data["id"]).first()
        assert sold_item is not None

        # Verify that the created sold item is linked to the correct sale
        assert "sale" in res.data
        assert str(res.data["sale"]) == str(sale.id)
        assert str(sold_item.sale.id) == (sale.id)

    def test_sold_item_created_by_authenticated_user(
        self,
        api_client,
        user,
        sold_item_data,
        sale
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        url = sold_item_url(sale.id)

        res = api_client.post(url, data=sold_item_data, format='json')
        assert res.status_code == 201

        # Verify that the sold item has been created
        assert "id" in res.data
        sold_item = SoldItem.objects.filter(id=res.data["id"]).first()
        assert sold_item is not None

        # Verify that the created sold item is linked to the correct user
        assert "created_by" in res.data
        assert res.data["created_by"] == user.username
        assert str(sold_item.created_by.id) == str(user.id)

    def test_list_sold_items_to_authenticated_user(
        self,
        api_client,
        user,
        sale
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create 5 sold items for the sale and authenticated user
        user_items = SoldItemFactory.create_batch(
            5, sale=sale, created_by=user
        )

        # Create 4 sold items for other sales and users
        SoldItemFactory.create_batch(4)

        url = sold_item_url(sale.id)

        res = api_client.get(url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == len(user_items)

        # Verify that all sold items belong to the correct sale and user
        assert all(
            str(item["sale"]) == str(sale.id)
            and item["created_by"] == user.username
            for item in res.data
        )

        user_item_ids = {str(item.id) for item in user_items}
        assert all(
            str(item["id"]) in user_item_ids
            for item in res.data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteSoldItemsView:
    """Test for the GetUpdateDeleteSoldItems view."""

    def test_get_update_delete_sold_item_view_requires_auth(
        self,
        api_client,
        sold_item,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = api_client.get(url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_sold_item_view_allowed_http_methods(
        self,
        auth_client,
        sold_item,
        sold_item_2,
        sold_item_data,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url, data=sold_item_data, format='json')
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url, data=sold_item_data, format='json')
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=sold_item_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_get_update_delete_sold_item_fails_with_non_existent_sale_id(
        self,
        auth_client,
        sold_item,
        random_uuid
    ):
        url = sold_item_url(random_uuid, sold_item.id)

        res = auth_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Sale with id '{random_uuid}' does not exist."

    def test_get_update_delete_sold_item_fails_with_unauthorized_sale(
        self,
        user,
        api_client,
        sold_item
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create another sale with a different user
        sale = SaleFactory.create()

        # Verify that the sale's created_by is different from the authenticated user
        assert str(sale.created_by.id) != str(user.id)

        url = sold_item_url(sale.id, sold_item.id)

        res = api_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Sale with id '{sale.id}' does not exist."

    def test_sold_item_operations_fail_with_nonexistent_sold_item_id(
        self,
        auth_client,
        random_uuid,
        sale
    ):
        url = sold_item_url(sale.id, random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == f"No SoldItem matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == f"No SoldItem matches the given query."

        # Test PATCH request
        patch_res = auth_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == f"No SoldItem matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == f"No SoldItem matches the given query."

    def test_get_sold_item_with_valid_id_and_sale_id(
        self,
        auth_client,
        sold_item,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200

    def test_sold_item_response_data_fields(
        self,
        auth_client,
        sold_item,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        expected_fields = {
            "id",
            "created_by",
            "sale",
            "item",
            "sold_quantity",
            "sold_price",
            "total_price",
            "total_profit",
            "unit_profit",
            "created_at",
            "updated_at"
        }

        assert expected_fields.issubset(res.data.keys())

    def test_sold_item_response_data_fields_types(
        self,
        auth_client,
        sold_item
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)
        res = auth_client.get(url)
        assert res.status_code == 200

        item_data = res.json()

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

    def test_sold_item_response_data_fields_values(
        self,
        auth_client,
        sold_item
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)
        res = auth_client.get(url)
        assert res.status_code == 200

        item_data = res.json()

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

    def test_sold_item_put_update(self, auth_client, sold_item, sold_item_data):
        sold_item_data["sold_price"] = sold_item.sold_price + 100

        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = auth_client.put(url, data=sold_item_data, format='json')
        assert res.status_code == 200
        res_data = res.json()
        
        # Verify that sold item has been updated
        assert "sold_price" in res_data
        assert res_data["sold_price"] == float(sold_item_data["sold_price"])

        sold_item.refresh_from_db()
        assert sold_item.sold_price == sold_item_data["sold_price"]

    def test_sold_item_patch_update(self,auth_client, sold_item):
        url = sold_item_url(sold_item.sale.id, sold_item.id)
        initial_sold_price = sold_item.sold_price

        res = auth_client.patch(
            url,
            data={"sold_price": initial_sold_price + 100},
            format='json'
        )

        assert res.status_code == 200
        res_data = res.json()
        
        # Verify that sold item has been updated
        assert "sold_price" in res_data
        assert res_data["sold_price"] == float(sold_item.sold_price + 100)

        sold_item.refresh_from_db()
        assert sold_item.sold_price == initial_sold_price + 100

    def test_sold_item_deletion_fails_for_delivered_sales(
        self,
        auth_client,
        sold_item,
        delivered_status,
    ):
        # Update sold item's sale status to delivered
        sold_item.sale.delivery_status = delivered_status
        sold_item.sale.save()

        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = auth_client.delete(url)
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot perform item deletion because the sale "
            f"with reference ID '{sold_item.sale.reference_id}' has "
            "already been marked as Delivered. Changes to delivered "
            f"sales' sold items are restricted to "
            "maintain data integrity."
        )

    def test_sold_item_deletion_fails_for_single_sold_item_in_a_sale(
        self,
        auth_client,
        sold_item,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        # Verify that the linked sale has only one sold item
        assert SoldItem.objects.filter(sale=sold_item.sale).count() == 1

        res = auth_client.delete(url)
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            "This item cannot be deleted because it is the only item in the "
            f"sale with reference ID '{sold_item.sale.reference_id}'. "
            "Every sale must have at least one item."
        )

    def test_successful_sold_item_deletion(
        self,
        auth_client,
        sold_item,
        sold_item_2
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the sold item has been deleted
        assert not SoldItem.objects.filter(id=sold_item.id).exists()

    def test_sold_item_deletion_resets_item_inventory_quantity(
        self,
        auth_client,
        sold_item,
        sold_item_2,
    ):
        url = sold_item_url(sold_item.sale.id, sold_item.id)

        inventory_item = sold_item.item
        initial_item_quantity = inventory_item.quantity

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the sold item has been deleted
        assert not SoldItem.objects.filter(id=sold_item.id).exists()

        # Verify that the item's quantity has been reset
        inventory_item.refresh_from_db()
        assert inventory_item.quantity != initial_item_quantity
        assert inventory_item.quantity == sold_item.sold_quantity + initial_item_quantity


@pytest.mark.django_db
class TestBulkDeleteSoldItemsView:
    """Tests for the bulk delete sold items view"""

    def test_bulk_delete_sold_items_view_requires_auth(
        self,
        api_client,
        sale
    ):
        url = bulk_delete_items_url(sale.id)
        res = api_client.delete(url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_sold_items_view_allowed_http_methods(
        self,
        auth_client,
        sold_item,
        sold_item_2
    ):
        url = bulk_delete_items_url(sold_item.sale.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 405
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "Method \"GET\" not allowed."

        post_res = auth_client.post(url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(
            url,
            data={"ids": [sold_item.id]},
            format="json"
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_sold_items_fails_with_nonexistent_sale_id(
        self,
        auth_client,
        random_uuid
    ):
        url = bulk_delete_items_url(random_uuid)

        res = auth_client.delete(
            url,
            data={"ids": []},
            format="json"
        )
        assert res.status_code == 404

        assert "detail" in res.data
        assert res.data["detail"] == (
            f"Sale with id '{random_uuid}' does not exist."
        )

    def test_bulk_delete_sold_items_fails_for_delivered_sales(
        self,
        auth_client,
        sold_item,
        sold_item_2,
        delivered_status
    ):
        # Update sold item's sale status to delivered
        sold_item.sale.delivery_status = delivered_status
        sold_item.sale.save()

        url = bulk_delete_items_url(sold_item.sale.id)

        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot perform item deletion because the sale "
            f"with reference ID '{sold_item.sale.reference_id}' has "
            "already been marked as Delivered. Changes to delivered "
            f"sales' sold items are restricted to "
            "maintain data integrity."
        )

    def test_bulk_delete_sold_items_fails_with_invalid_uuids(
        self,
        auth_client,
        sale,
        sold_item,
    ):
        url = bulk_delete_items_url(sale.id)

        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id, "invalid_uuid_1", "invalid_uuid_2"]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid uuids."

        assert "invalid_uuids" in res_error
        assert "invalid_uuid_1" in res_error["invalid_uuids"]
        assert "invalid_uuid_2" in res_error["invalid_uuids"]

    def test_bulk_delete_sold_items_fails_for_nonexistent_uuids(
        self,
        auth_client,
        sale,
        sold_item,
    ):
        random_uuid_1 = str(uuid.uuid4())
        random_uuid_2 = str(uuid.uuid4())

        url = bulk_delete_items_url(sale.id)

        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id, random_uuid_1, random_uuid_2]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not found."

        assert "missing_ids" in res_error
        assert random_uuid_1 in res_error["missing_ids"]
        assert random_uuid_2 in res_error["missing_ids"]

    def test_bulk_delete_sold_items_fails_for_all_sold_items(
        self,
        auth_client,
        sale,
        sold_item,
        sold_item_2,
    ):
        # Verify that both sold items belong to the specified sale
        assert str(sold_item.sale.id) == str(sale.id)
        assert str(sold_item_2.sale.id) == str(sale.id)

        # Verify that the sale only has the two sold items
        assert len(sale.sold_items.all()) == 2

        url = bulk_delete_items_url(sale.id)

        # Try to delete both sold items
        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id, sold_item_2.id]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot delete items from sale with reference ID "
            f"'{sale.reference_id}' as it would leave no items linked. "
            f"Each sale must have at least one item."
        )

    def test_bulk_delete_sold_items_succeeds(
        self,
        auth_client,
        sale,
        sold_item,
        sold_item_2,
    ):
        # Verify that both sold items belong to the specified sale
        assert str(sold_item.sale.id) == str(sale.id)
        assert str(sold_item_2.sale.id) == str(sale.id)

        # Create a third sold item to prevent sale with no items linked error
        sold_item_3 = SoldItemFactory.create(
            created_by=sale.created_by,
            sale=sale
        )

        # Verify that the sale has three sold items
        assert len(sale.sold_items.all()) == 3

        url = bulk_delete_items_url(sale.id)

        # Try to delete two sold items
        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id, sold_item_2.id]},
            format="json"
        )
        assert res.status_code == 200

        assert "message" in res.data
        assert res.data["message"] == "2 sold items successfully deleted."

        # Verify that the two sold items have been deleted
        assert not SoldItem.objects.filter(
            id__in=[sold_item.id, sold_item_2.id]
        ).exists()

        # Verify that the sale still has one linked sold item
        sale.refresh_from_db()
        assert len(sale.sold_items.all()) == 1
        assert SoldItem.objects.filter(sale=sale).exists()
        assert SoldItem.objects.filter(id=sold_item_3.id).exists()

    def test_bulk_delete_sold_items_resets_items_inventory_quantities(
        self,
        auth_client,
        sale,
        sold_item,
        sold_item_2,
    ):
        # Verify that both sold items belong to the specified sale
        assert str(sold_item.sale.id) == str(sale.id)
        assert str(sold_item_2.sale.id) == str(sale.id)

        # Get sold items linked inventory items quantities
        inventory_item_1 = sold_item.item
        initial_item_1_quantity = inventory_item_1.quantity

        inventory_item_2 = sold_item_2.item
        initial_item_2_quantity = inventory_item_2.quantity

        # Create a third sold item to prevent sale with no items linked error
        SoldItemFactory.create(
            created_by=sale.created_by,
            sale=sale
        )

        # Verify that the sale has three sold items
        assert len(sale.sold_items.all()) == 3

        url = bulk_delete_items_url(sale.id)

        # Try to delete two sold items
        res = auth_client.delete(
            url,
            data={"ids": [sold_item.id, sold_item_2.id]},
            format="json"
        )
        assert res.status_code == 200

        assert "message" in res.data
        assert res.data["message"] == "2 sold items successfully deleted."

        #  Verify that the sold items have been deleted
        assert not SoldItem.objects.filter(
            id__in=[sold_item.id, sold_item_2.id]
        ).exists()

        # Verify that the items inventory's quantities have been reset
        inventory_item_1.refresh_from_db()
        assert inventory_item_1.quantity != initial_item_1_quantity
        assert inventory_item_1.quantity == (
            initial_item_1_quantity + sold_item.sold_quantity
        )

        inventory_item_2.refresh_from_db()
        assert inventory_item_2.quantity != initial_item_2_quantity
        assert inventory_item_2.quantity == (
            initial_item_2_quantity + sold_item_2.sold_quantity
        )

