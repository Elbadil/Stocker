import pytest
import uuid
import random
from typing import Union
from django.urls import reverse
from apps.base.models import Activity
from apps.inventory.factories import ItemFactory
from apps.client_orders.factories import OrderStatusFactory
from apps.supplier_orders.models import (
    Supplier,
    SupplierOrder,
    SupplierOrderedItem
)
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderedItemFactory,
    SupplierOrderFactory
)
from utils.serializers import date_repr_format, get_location
from utils.status import (
    DELIVERY_STATUS_OPTIONS,
    PAYMENT_STATUS_OPTIONS,
    COMPLETED_STATUS,
    FAILED_STATUS,
    ACTIVE_DELIVERY_STATUS
)

@pytest.fixture
def create_list_supplier_url():
    return reverse('create_list_suppliers')

@pytest.fixture
def bulk_delete_suppliers_url():
    return reverse('bulk_delete_suppliers')

def supplier_url(supplier_id: str):
    return reverse('get_update_delete_suppliers', kwargs={"id": supplier_id})

@pytest.fixture
def create_list_orders_url():
    return reverse('create_list_supplier_orders')

@pytest.fixture
def bulk_delete_orders_url():
    return reverse('bulk_delete_supplier_orders')

def order_url(order_id: str):
    return reverse('get_update_delete_supplier_orders', kwargs={"id": order_id})

def ordered_item_url(order_id: str, item_id: Union[str, None]=None):
    """
    Returns the URL for the create_list_supplier_ordered_items or
    get_update_delete_supplier_ordered_items view based on the provided order ID
    and optionally item ID.
    """
    if item_id:
        return reverse("get_update_delete_supplier_ordered_items",
                       kwargs={"order_id": order_id, "id": item_id})
    return reverse("create_list_supplier_ordered_items",
                   kwargs={"order_id": order_id})


def bulk_delete_items_url(order_id: str):
    return reverse("bulk_delete_supplier_ordered_items",
                   kwargs={"order_id": order_id})

@pytest.fixture
def supplier_orders_data_url():
    return reverse('get_supplier_orders_data')


@pytest.mark.django_db
class TestCreateListSuppliersView:
    """Tests for the create and list supplier view"""

    def test_create_list_suppliers_view_requires_auth(
        self,
        api_client,
        create_list_supplier_url
    ):
        res = api_client.get(create_list_supplier_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_suppliers_view_allowed_http_methods(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        get_res = auth_client.get(create_list_supplier_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert post_res.status_code == 201

        put_res = auth_client.put(create_list_supplier_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(create_list_supplier_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(create_list_supplier_url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_create_supplier_fails_without_name(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        supplier_data.pop("name")
        res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("This field is required.")

    def test_create_supplier_fails_with_blank_name(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        supplier_data["name"] = ""
        res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("This field may not be blank.")

    def test_create_supplier_fails_with_existing_name(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        SupplierFactory.create(name="Supplier 1")
        supplier_data["name"] = "Supplier 1"
        res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("supplier with this name already exists.")

    def test_create_supplier_fails_with_invalid_email(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        supplier_data["email"] = "invalid_email"
        res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"][0].startswith("Enter a valid email address.")

    def test_create_supplier_with_valid_data(
        self,
        auth_client,
        supplier_data,
        create_list_supplier_url
    ):
        res = auth_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 201
        assert res.data["name"] == supplier_data["name"]
        
        # Verify supplier was created
        supplier = Supplier.objects.filter(name=supplier_data["name"]).first()
        assert supplier is not None
        assert supplier.name == supplier_data["name"]

    def test_supplier_created_by_authenticated_user(
        self,
        user,
        api_client,
        supplier_data,
        create_list_supplier_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        res = api_client.post(
            create_list_supplier_url,
            data=supplier_data,
            format="json"
        )
        assert res.status_code == 201
        
        # Verify the created supplier is associated with the authenticated user
        supplier = Supplier.objects.filter(name=supplier_data["name"]).first()
        assert supplier is not None
        assert str(supplier.created_by.id) == str(user.id)

    def test_list_suppliers_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_supplier_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 7 suppliers for the authenticated user
        user_suppliers = SupplierFactory.create_batch(7, created_by=user)

        # Create 3 suppliers for other users
        SupplierFactory.create_batch(3)

        res = api_client.get(create_list_supplier_url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == 7

        # Verify that all suppliers belong to the authenticated user
        assert all(supplier["created_by"] == str(user.username)
                   for supplier in res.data)

        user_supplier_ids = set(str(supplier.id) for supplier in user_suppliers)
        assert all(
            supplier["id"] in user_supplier_ids
            for supplier in res.data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteSuppliersView:
    """Tests for the get update delete suppliers view."""

    def test_get_update_delete_suppliers_view_requires_auth(
        self,
        api_client,
        supplier,
    ):
        res = api_client.get(supplier_url(supplier.id))
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_suppliers_view_allowed_http_methods(
        self,
        auth_client,
        supplier,
        supplier_data,
    ):
        url = supplier_url(supplier.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url, data=supplier_data, format='json')
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=supplier_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_supplier_operations_fail_with_inexistent_id(self, auth_client, random_uuid):
        url = supplier_url(random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Supplier matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No Supplier matches the given query."

        # Test PATCH request
        patch_res = auth_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No Supplier matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No Supplier matches the given query."

    def test_supplier_operations_fail_with_supplier_not_linked_to_authenticated_user(
        self,
        user,
        api_client
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create a supplier without linking it to the authenticated user
        supplier = SupplierFactory.create()
        url = supplier_url(supplier.id)

        # Verify that the supplier does not belong to the authenticated user
        assert str(supplier.created_by.id) != str(user.id)

        # Test GET request
        get_res = api_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Supplier matches the given query."

        # Test PUT request
        put_res = api_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No Supplier matches the given query."

        # Test PATCH request
        patch_res = api_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No Supplier matches the given query."

        # Test DELETE request
        delete_res = api_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No Supplier matches the given query."

    def test_get_supplier_with_valid_supplier(self, user, api_client, supplier):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Verify that the supplier belongs to the authenticated user
        assert str(supplier.created_by.id) == str(user.id)

        url = supplier_url(supplier.id)
        res = api_client.get(url)
        assert res.status_code == 200

    def test_supplier_response_data_fields(self, auth_client, supplier):
        url = supplier_url(supplier.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        expected_fields = {
            "id",
            "created_by",
            "name",
            "phone_number",
            "email",
            "location",
            "total_orders",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(res.data.keys())

    def test_supplier_response_data_fields_types(self, auth_client, supplier):
        res = auth_client.get(supplier_url(supplier.id))
        assert res.status_code == 200

        assert isinstance(res.data["id"], str)
        assert isinstance(res.data["created_by"], str)
        assert isinstance(res.data["name"], str)
        assert isinstance(res.data["phone_number"], str)
        assert isinstance(res.data["email"], str)
        assert isinstance(res.data["location"], dict)
        assert isinstance(res.data["total_orders"], int)
        assert isinstance(res.data["created_at"], str)
        assert isinstance(res.data["updated_at"], str)
        assert isinstance(res.data["updated"], bool)

    def test_supplier_response_data_fields_values(self, auth_client, supplier):
        res = auth_client.get(supplier_url(supplier.id))
        assert res.status_code == 200

        assert res.data["id"] == str(supplier.id)
        assert res.data["created_by"] == supplier.created_by.username
        assert res.data["name"] == supplier.name
        assert res.data["phone_number"] == supplier.phone_number
        assert res.data["email"] == supplier.email
        assert res.data["location"] == get_location(supplier.location)
        assert res.data["total_orders"] == supplier.total_orders
        assert res.data["created_at"] == date_repr_format(supplier.created_at)
        assert res.data["updated_at"] == date_repr_format(supplier.updated_at)
        assert res.data["updated"] == supplier.updated

    def test_supplier_put_update(self, auth_client, supplier):
        supplier_data = {
            "name": "Supplier 2",
            "email": "Y6V8b@example.com",
        }

        assert supplier.name != supplier_data["name"]
        assert supplier.email != supplier_data["email"]

        url = supplier_url(supplier.id)
        res = auth_client.put(url, data=supplier_data, format='json')
        assert res.status_code == 200

        # Verify supplier was updated
        assert res.data["name"] == supplier_data["name"]
        assert res.data["email"] == supplier_data["email"]

        supplier.refresh_from_db()
        assert supplier.name == supplier_data["name"]
        assert supplier.email == supplier_data["email"]

    def test_supplier_patch_update(self, auth_client, supplier):
        supplier_data = {
            "email": "Y6V8b@example.com",
        }

        assert supplier.email != supplier_data["email"]

        url = supplier_url(supplier.id)
        res = auth_client.patch(url, data=supplier_data, format='json')
        assert res.status_code == 200

        # Verify supplier was updated
        assert res.data["email"] == supplier_data["email"]

        supplier.refresh_from_db()
        assert supplier.email == supplier_data["email"]

    def test_supplier_deletion_fails_with_linked_orders(
        self,
        auth_client,
        supplier,
        supplier_order
    ):
        # Verify that the supplier has linked orders
        assert supplier.total_orders > 0
        assert str(supplier_order.supplier.id) == str(supplier.id)

        url = supplier_url(supplier.id)
        res = auth_client.delete(url)
        assert res.status_code == 400
        
        assert "error" in res.data
        assert res.data["error"] == (
            f"Supplier {supplier.name} is linked to existing orders. "
            "Manage orders before deletion."
        )

        # Verify that the supplier record has not been deleted
        supplier.refresh_from_db()
        assert Supplier.objects.filter(id=supplier.id).exists()

    def test_supplier_successful_deletion(self, auth_client, supplier):
        # Verify that the supplier has no linked orders
        assert supplier.total_orders == 0

        url = supplier_url(supplier.id)
        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the supplier record has been deleted
        assert not Supplier.objects.filter(id=supplier.id).exists()

    def test_supplier_deletion_registers_a_new_activity(self, auth_client, supplier):
        # Verify that there's no delete activity for the supplier
        assert not Activity.objects.filter(
            action="deleted",
            model_name="supplier",
            object_ref__contains=[supplier.name]
        ).exists()

        # Verify that the supplier has no linked orders
        assert supplier.total_orders == 0

        url = supplier_url(supplier.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the supplier record has been deleted
        assert not Supplier.objects.filter(id=supplier.id).exists()

        # Verify that an activity record has been created for the supplier deletion
        assert (
            Activity.objects.filter(
                action="deleted",
                model_name="supplier",
                object_ref__contains=[supplier.name]
            ).exists()
        )


@pytest.mark.django_db
class TestBulkDeleteSuppliersView:
    """Tests for the bulk delete suppliers view."""

    def test_bulk_delete_suppliers_view_requires_auth(
        self,
        api_client,
        bulk_delete_suppliers_url
    ):
        res = api_client.delete(bulk_delete_suppliers_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_suppliers_view_allowed_http_methods(
        self,
        auth_client,
        supplier,
        bulk_delete_suppliers_url
    ):
        get_res = auth_client.get(bulk_delete_suppliers_url)
        assert get_res.status_code == 405
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "Method \"GET\" not allowed."

        post_res = auth_client.post(bulk_delete_suppliers_url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(bulk_delete_suppliers_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(bulk_delete_suppliers_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id]},
            format="json"
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_suppliers_fails_without_list_of_ids(
        self,
        auth_client,
        bulk_delete_suppliers_url
    ):
        res = auth_client.delete(bulk_delete_suppliers_url, data={}, format="json")
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_suppliers_fails_with_empty_ids_list(
        self,
        auth_client,
        bulk_delete_suppliers_url
    ):
        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": []},
            format="json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_suppliers_fails_with_invalid_uuids(
        self,
        supplier,
        auth_client,
        bulk_delete_suppliers_url
    ):
        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, "invalid_uuid"]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid UUIDs."
        
        assert "invalid_uuids" in res_error
        assert len(res_error["invalid_uuids"]) == 1
        assert res_error["invalid_uuids"] == ["invalid_uuid"]

    def test_bulk_delete_suppliers_fails_with_inexistent_ids(
        self,
        supplier,
        auth_client,
        bulk_delete_suppliers_url
    ):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, random_id_1, random_id_2]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all suppliers could not be found."

        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == 2
        assert random_id_1 in missing_ids
        assert random_id_2 in missing_ids

    def test_bulk_delete_suppliers_fails_with_unauthorized_suppliers(
        self,
        user,
        api_client,
        bulk_delete_suppliers_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 3 suppliers for the authenticated user
        user_suppliers = SupplierFactory.create_batch(3, created_by=user)

        # Create 2 suppliers for other users
        other_suppliers = SupplierFactory.create_batch(2)

        all_suppliers = user_suppliers + other_suppliers
        res = api_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id for supplier in all_suppliers]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all suppliers could not be found."

        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == len(other_suppliers)
        assert all(str(supplier.id) in missing_ids for supplier in other_suppliers)

    def bulk_delete_suppliers_fails_with_all_suppliers_linked_to_orders(
        self,
        user,
        supplier,
        auth_client,
        bulk_delete_suppliers_url,
        supplier_order
    ):
        # Create a second supplier and link it to another order
        supplier_2 = SupplierFactory.create(created_by=user)
        supplier_order_2 = SupplierOrderFactory.create(supplier=supplier_2)

        # Verify that both suppliers are linked to orders
        assert supplier.total_orders > 0
        assert supplier_2.total_orders > 0

        # Current suppliers list
        suppliers = [
            {
                "id": supplier.id,
                "name": supplier.name
            },
            {
                "id": supplier_2.id,
                "name": supplier_2.name
            }
        ]

        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, supplier_2.id]},
            format='json'
        )
        assert res.status_code == 400

        res_data = res.json()
        assert "error" in res_data
        res_error = res_data["error"]

        assert "message" in res_error
        assert res_error["message"] == (
            "All selected suppliers are linked to existing orders. "
            "Manage orders before deletion."
        )

        assert "linked_suppliers" in res_error
        assert len(res_error["linked_suppliers"]) == 2

        assert suppliers[0] in res_error["linked_suppliers"]
        assert suppliers[1] in res_error["linked_suppliers"]

    def test_bulk_delete_suppliers_with_some_suppliers_linked_to_orders_and_others_not(
        self,
        user,
        auth_client,
        bulk_delete_suppliers_url,
        supplier
    ):
        # Create a second supplier without linking it to an order
        supplier_2 = SupplierFactory.create(created_by=user)
        
        # Create a third supplier and link it to another order
        supplier_3 = SupplierFactory.create(created_by=user)
        supplier_order = SupplierOrderFactory.create(supplier=supplier_3)

        # Verify that supplier and supplier_2 are not linked to orders
        assert supplier.total_orders == 0
        assert supplier_2.total_orders == 0

        # Verify that supplier_3 is linked to an order
        assert supplier_3.total_orders > 0

        supplier_with_order = {
            "id": supplier_3.id,
            "name": supplier_3.name
        }

        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, supplier_2.id, supplier_3.id]},
            format='json'
        )
        assert res.status_code == 207
        res_data = res.json()

        assert "message" in res_data
        assert res_data["message"] == (
            "2 suppliers deleted successfully, but 1 supplier could not be deleted "
            "because they are linked to existing orders."
        )

        assert "linked_suppliers" in res_data
        assert len(res_data["linked_suppliers"]) == 1
        assert supplier_with_order in res_data["linked_suppliers"]

        # Verify that the two suppliers were deleted
        assert not Supplier.objects.filter(id__in=[supplier.id, supplier_2.id]).exists()

        # Verify that supplier_3 was not not deleted
        assert Supplier.objects.filter(id=supplier_3.id).exists()

    def test_bulk_delete_suppliers_succeeds_with_all_suppliers_not_linked_to_orders(
        self,
        user,
        auth_client,
        bulk_delete_suppliers_url,
        supplier
    ):
        # Create a second supplier without linking it to an order
        supplier_2 = SupplierFactory.create(created_by=user)

        # Verify that both suppliers are not linked to orders
        assert supplier.total_orders == 0
        assert supplier_2.total_orders == 0

        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, supplier_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 suppliers successfully deleted."

        # Verify that both suppliers were deleted
        assert not Supplier.objects.filter(id__in=[supplier.id, supplier_2.id]).exists()
    
    def test_bulk_delete_suppliers_registers_a_new_activity(
        self,
        user,
        auth_client,
        bulk_delete_suppliers_url,
        supplier
    ):
        # Create a second supplier without linking it to an order
        supplier_2 = SupplierFactory.create(created_by=user)

        # Verify that there's no delete activity for the two suppliers
        assert not Activity.objects.filter(
            action="deleted",
            model_name="supplier",
            object_ref__contains=[supplier.name, supplier_2.name]
        ).exists()

        # Verify that both suppliers are not linked to orders
        assert supplier.total_orders == 0
        assert supplier_2.total_orders == 0

        res = auth_client.delete(
            bulk_delete_suppliers_url,
            data={"ids": [supplier.id, supplier_2.id]},
            format='json'
        )
        assert res.status_code == 200

        # Verify that both suppliers were deleted
        assert not Supplier.objects.filter(id__in=[supplier.id, supplier_2.id]).exists()

        # Verify that an activity record has been created for the suppliers deletion
        assert Activity.objects.filter(
            action="deleted",
            model_name="supplier",
            object_ref__contains=[supplier.name, supplier_2.name]
        ).exists()


@pytest.mark.django_db
class TestCreateListSupplierOrdersView:
    """Tests for the create list supplier orders view"""
   
    def test_create_list_supplier_orders_view_requires_auth(
        self,
        api_client,
        create_list_orders_url
    ):
        res = api_client.get(create_list_orders_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_supplier_orders_view_allowed_http_methods(
        self,
        auth_client,
        order_data,
        create_list_orders_url
    ):
        get_res = auth_client.get(create_list_orders_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(
            create_list_orders_url,
            data=order_data,
            format='json'
        )
        assert post_res.status_code == 201

        put_res = auth_client.put(create_list_orders_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(create_list_orders_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(create_list_orders_url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_successful_order_creation(
        self,
        auth_client,
        order_data,
        create_list_orders_url
    ):
        res = auth_client.post(
            create_list_orders_url,
            data=order_data,
            format='json'
        )
        assert res.status_code == 201

        res_data = res.json()

        # Verify that the order was created
        assert "id" in res_data
        assert SupplierOrder.objects.filter(id=res_data["id"]).exists()
    
    def test_order_created_by_authenticated_user(
        self,
        user,
        api_client,
        order_data,
        create_list_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        res = api_client.post(
            create_list_orders_url,
            data=order_data,
            format='json'
        )
        assert res.status_code == 201

        res_data = res.json()
        assert "id" in res_data

        # Verify that the order was created
        order = SupplierOrder.objects.filter(id=res_data["id"]).first()
        assert order is not None

        # Verify that the order was created by the authenticated user
        assert str(order.created_by.id) == str(user.id)

    def test_list_orders_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 7 orders for the authenticated user
        user_orders = SupplierOrderFactory.create_batch(7, created_by=user)

        # Create 5 orders for other users
        SupplierOrderFactory.create_batch(5)

        res = api_client.get(create_list_orders_url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == 7

        # Verify that all orders belong to the authenticated user
        assert all(order["created_by"] == str(user.username)
                   for order in res.data)

        user_orders_ids = {str(order.id) for order in user_orders}
        assert all(
            order["id"] in user_orders_ids
            for order in res.data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteSupplierOrdersView:
    """Tests for the get update delete supplier orders view"""

    def test_get_update_delete_orders_view_requires_auth(
        self,
        api_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)
        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_orders_view_allowed_http_methods(
        self,
        auth_client,
        supplier_order,
        order_data
    ):
        url = order_url(supplier_order.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url, data=order_data, format='json')
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=order_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_order_operations_fail_with_inexistent_order_id(
        self,
        auth_client,
        random_uuid,
        order_data
    ):
        url = order_url(random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data=order_data, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test PATCH request
        patch_res = auth_client.patch(url, data=order_data, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No SupplierOrder matches the given query."

    def test_order_operations_fail_with_order_not_linked_to_authenticated_user(
        self,
        user,
        api_client,
        order_data
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create an order without linking it to the authenticated user
        order = SupplierOrderFactory.create()
        url = order_url(order.id)

        # Verify that the order does not belong to the authenticated user
        assert str(order.created_by.id) != str(user.id)

        # Test GET request
        get_res = api_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test PUT request
        put_res = api_client.put(url, data=order_data, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test PATCH request
        patch_res = api_client.patch(url, data=order_data, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No SupplierOrder matches the given query."

        # Test DELETE request
        delete_res = api_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No SupplierOrder matches the given query."

    def test_get_order_with_valid_order_id(
        self,
        user,
        api_client,
        supplier_order
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        url = order_url(supplier_order.id)

        # Verify that the order belongs to the authenticated user
        assert str(supplier_order.created_by.id) == str(user.id)

        res = api_client.get(url)
        assert res.status_code == 200

    def test_order_response_data_fields(self, auth_client, supplier_order):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()
        
        expected_fields = {
            "id",
            "reference_id",
            "created_by",
            "supplier",
            "ordered_items",
            'total_quantity',
            'total_price',
            "delivery_status",
            "payment_status",
            "tracking_number",
            "shipping_cost",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(res_data.keys())

    def test_order_response_data_fields_types(
        self,
        auth_client,
        supplier_order,
        ordered_item
    ):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert isinstance(res_data['id'], str)
        assert isinstance(res_data['reference_id'], str)
        assert isinstance(res_data['created_by'], str)
        assert isinstance(res_data['supplier'], str)
        assert isinstance(res_data['ordered_items'], list)
        assert isinstance(res_data['total_quantity'], int)
        assert isinstance(res_data['total_price'], float)
        assert isinstance(res_data['delivery_status'], str)
        assert isinstance(res_data['payment_status'], str)
        assert isinstance(res_data['tracking_number'], str)
        assert isinstance(res_data['shipping_cost'], float)
        assert isinstance(res_data['created_at'], str)
        assert isinstance(res_data['updated_at'], str)
        assert isinstance(res_data['updated'], bool)

    def test_order_response_data_for_general_fields(
        self,
        auth_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data['id'] == str(supplier_order.id)
        assert res_data['reference_id'] == supplier_order.reference_id
        assert res_data['created_by'] == supplier_order.created_by.username
        assert res_data['supplier'] == supplier_order.supplier.name
        assert res_data["updated"] == supplier_order.updated

    def test_order_response_data_for_ordered_items_field(
        self,
        auth_client,
        supplier_order,
        ordered_item
    ):
        # Verify that ordered_item belongs to supplier_order
        assert str(supplier_order.id) == str(ordered_item.order.id)

        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data['ordered_items'][0]['id'] == ordered_item.id
        assert res_data['ordered_items'][0]['item'] == ordered_item.item.name
        assert res_data['ordered_items'][0]['ordered_quantity'] == ordered_item.ordered_quantity
        assert res_data['ordered_items'][0]['ordered_price'] == float(ordered_item.ordered_price)
        assert res_data['ordered_items'][0]['total_price'] == float(ordered_item.total_price)
        assert res_data['ordered_items'][0]['in_inventory'] == ordered_item.in_inventory

    def test_order_response_data_for_financial_fields(
        self,
        auth_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data['total_quantity'] == supplier_order.total_quantity
        assert res_data['total_price'] == float(supplier_order.total_price)
        assert res_data['shipping_cost'] == float(supplier_order.shipping_cost)

    def test_order_response_data_for_status_fields(
        self,
        auth_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data['delivery_status'] == supplier_order.delivery_status.name
        assert res_data['payment_status'] == supplier_order.payment_status.name

    def test_order_response_data_for_date_fields(
        self,
        auth_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data['created_at'] == date_repr_format(supplier_order.created_at)
        assert res_data['updated_at'] == date_repr_format(supplier_order.updated_at)

    def test_order_put_update(
        self,
        auth_client,
        supplier_order,
        delivered_status,
        order_data
    ):
        # Verify that order's delivery status and tracking number are different
        # than the exiting ones
        order_data["delivery_status"] = delivered_status.name
        order_data["tracking_number"] = "123456789"

        # Verify that order_data is different from supplier_order data
        assert order_data["delivery_status"] != supplier_order.delivery_status.name
        assert order_data["tracking_number"] != supplier_order.tracking_number

        url = order_url(supplier_order.id)

        res = auth_client.put(
            url,
            data=order_data,
            format='json'
        )
        assert res.status_code == 200
        res_data = res.json()

        # Verify that order was updated
        assert res_data["delivery_status"] == order_data["delivery_status"]
        assert res_data["tracking_number"] == order_data["tracking_number"]

        # Verify that order record has been updated
        supplier_order.refresh_from_db()
        assert supplier_order.delivery_status.name == order_data["delivery_status"]
        assert supplier_order.tracking_number == order_data["tracking_number"]

    def test_order_patch_update(
        self,
        auth_client,
        supplier_order,
        delivered_status,
    ):
        # Verify that order's delivery status and tracking number are different
        # than the exiting ones
        order_data = {
            "delivery_status": delivered_status.name,
            "tracking_number": "123456789",
        }

        # Verify that order_data is different from supplier_order data
        assert order_data["delivery_status"] != supplier_order.delivery_status.name
        assert order_data["tracking_number"] != supplier_order.tracking_number

        url = order_url(supplier_order.id)

        res = auth_client.patch(
            url,
            data=order_data,
            format='json'
        )
        assert res.status_code == 200
        res_data = res.json()

        # Verify that order was updated
        assert res_data["delivery_status"] == order_data["delivery_status"]
        assert res_data["tracking_number"] == order_data["tracking_number"]

        # Verify that order record has been updated
        supplier_order.refresh_from_db()
        assert supplier_order.delivery_status.name == order_data["delivery_status"]
        assert supplier_order.tracking_number == order_data["tracking_number"]

    def test_order_deletion(
        self,
        auth_client,
        supplier_order
    ):
        url = order_url(supplier_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that order record has been deleted
        assert not SupplierOrder.objects.filter(id=supplier_order.id).exists()

    def test_order_deletion_deletes_linked_ordered_items(
        self,
        auth_client,
        supplier_order,
        ordered_item,
    ):
        # Create a second ordered item and link it to the order
        ordered_item_2 = SupplierOrderedItemFactory.create(
            created_by=supplier_order.created_by,
            order=supplier_order
        )

        # Verify that both ordered items belong to the specified order
        assert str(ordered_item.order.id) == str(supplier_order.id)
        assert str(ordered_item_2.order.id) == str(supplier_order.id)

        url = order_url(supplier_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that order record has been deleted
        assert not SupplierOrder.objects.filter(id=supplier_order.id).exists()

        # Verify that linked ordered items records have been deleted
        assert not SupplierOrderedItem.objects.filter(order__id=supplier_order.id).exists()

    def test_order_deletion_registers_a_new_activity(
        self,
        auth_client,
        supplier_order
    ):
        # Verify that there's no delete activity for the order
        assert not Activity.objects.filter(
            action="deleted",
            model_name="supplier order",
            object_ref__contains=[supplier_order.reference_id]
        ).exists()

        url = order_url(supplier_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the order record has been deleted
        assert not SupplierOrder.objects.filter(id=supplier_order.id).exists()

        # Verify that there's a delete activity for the order
        assert Activity.objects.filter(
            action="deleted",
            model_name="supplier order",
            object_ref__contains=[supplier_order.reference_id]
        ).exists()


@pytest.mark.django_db
class TestBulkDeleteSupplierOrdersView:
    """Tests for the bulk delete supplier orders view."""

    def test_bulk_delete_orders_view_requires_auth(self, api_client, bulk_delete_orders_url):
        res = api_client.delete(bulk_delete_orders_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_orders_view_allowed_http_methods(
        self,
        auth_client,
        supplier_order,
        bulk_delete_orders_url
    ):
        get_res = auth_client.get(bulk_delete_orders_url)
        assert get_res.status_code == 405
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "Method \"GET\" not allowed."

        post_res = auth_client.post(bulk_delete_orders_url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        patch_res = auth_client.patch(bulk_delete_orders_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [supplier_order.id]},
            format="json"
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_orders_fails_without_ids_list(
        self,
        auth_client,
        bulk_delete_orders_url
    ):
        res = auth_client.delete(bulk_delete_orders_url)
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_orders_fails_with_empty_ids_list(
        self,
        auth_client,
        bulk_delete_orders_url
    ):
        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": []},
            format="json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_orders_fails_with_invalid_uuids(
        self,
        auth_client,
        supplier_order,
        bulk_delete_orders_url
    ):
        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [supplier_order.id, "invalid_uuid"]},
            format="json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]
        assert res_error["message"] == "Some or all provided IDs are not valid uuids."
        assert len(res_error["invalid_ids"]) == 1
        assert res_error["invalid_ids"] == ["invalid_uuid"]

    def test_bulk_delete_orders_fails_with_inexistent_ids(
        self,
        auth_client,
        supplier_order,
        bulk_delete_orders_url
    ):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [supplier_order.id, random_id_1, random_id_2]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all selected orders could not be found."

        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == 2
        assert random_id_1 in missing_ids
        assert random_id_2 in missing_ids

    def test_bulk_delete_orders_fails_with_unauthorized_orders(
        self,
        user,
        api_client,
        bulk_delete_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 3 orders for the authenticated user
        user_orders = SupplierOrderFactory.create_batch(3, created_by=user)

        # Create 2 orders for other users
        other_orders = SupplierOrderFactory.create_batch(2)

        all_orders = user_orders + other_orders
        res = api_client.delete(
            bulk_delete_orders_url,
            data={"ids": [order.id for order in all_orders]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all selected orders could not be found."

        assert "missing_ids" in res_error
        assert len(res_error["missing_ids"]) == len(other_orders)
        assert all(str(order.id) in res_error["missing_ids"] for order in other_orders)

    def test_bulk_delete_orders_succeeds_with_valid_orders(
        self,
        user,
        api_client,
        bulk_delete_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 3 orders for the authenticated user
        user_orders = SupplierOrderFactory.create_batch(3, created_by=user)

        res = api_client.delete(
            bulk_delete_orders_url,
            data={"ids": [order.id for order in user_orders]},
            format='json'
        )
        assert res.status_code == 200

        # Verify that the orders were deleted
        assert not SupplierOrder.objects.filter(
            id__in=[order.id for order in user_orders]
        ).exists()

        assert "message" in res.data
        assert res.data["message"] == (
            f"{len(user_orders)} supplier orders successfully deleted."
        )

    def test_bulk_delete_orders_deletes_linked_ordered_items(
        self,
        user,
        api_client,
        bulk_delete_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create two orders for the authenticated user with ordered item
        order_1 = SupplierOrderFactory.create(created_by=user)
        SupplierOrderedItemFactory.create_batch(
            3, created_by=user, order=order_1
        )

        order_2 = SupplierOrderFactory.create(created_by=user)
        SupplierOrderedItemFactory.create_batch(
            2, created_by=user, order=order_2
        )

        res = api_client.delete(
            bulk_delete_orders_url,
            data={"ids": [order_1.id, order_2.id]},
            format='json'
        )
        assert res.status_code == 200

        # Verify that the orders were deleted
        assert not SupplierOrder.objects.filter(
            id__in=[order_1.id, order_2.id]
        ).exists()

        assert "message" in res.data
        assert res.data["message"] == (
            f"2 supplier orders successfully deleted."
        )

        # Verify that linked ordered items were deleted
        assert not SupplierOrderedItem.objects.filter(
            order__id__in=[order_1.id, order_2.id]
        ).exists()

    def test_bulk_delete_orders_registers_a_new_activity(
        self,
        user,
        api_client,
        bulk_delete_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create orders for the authenticated user
        order_1 = SupplierOrderFactory.create(created_by=user)
        order_2 = SupplierOrderFactory.create(created_by=user)
    
        # Verify that there's no delete activity for the orders
        assert not Activity.objects.filter(
            action="deleted",
            model_name="supplier order",
            object_ref__contains=[order_1.reference_id, order_2.reference_id]
        ).exists()

        res = api_client.delete(
            bulk_delete_orders_url,
            data={"ids": [order_1.id, order_2.id]},
            format='json'
        )
        assert res.status_code == 200

        # Verify that the orders were deleted
        assert not SupplierOrder.objects.filter(
            id__in=[order.id for order in SupplierOrder.objects.all()]
        ).exists()

        assert "message" in res.data
        assert res.data["message"] == (
            f"2 supplier orders successfully deleted."
        )

        # Verify that an activity was created
        assert Activity.objects.filter(
            action="deleted",
            model_name="supplier order",
            object_ref__contains=[order_1.reference_id, order_2.reference_id]
        ).exists()


@pytest.mark.django_db
class TestCreateListSupplierOrderedItemsView:
    """Tests for the create list supplier ordered items view."""

    def test_create_list_ordered_items_view_requires_auth(
        self,
        api_client,
        supplier_order
    ):
        url = ordered_item_url(supplier_order.id)

        res = api_client.get(url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_ordered_items_view_allowed_http_methods(
        self,
        auth_client,
        supplier_order,
        ordered_item_data
    ):
        url = ordered_item_url(supplier_order.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url, data=ordered_item_data, format='json')
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

    def test_create_list_ordered_items_fails_with_nonexistent_order_id(
        self,
        auth_client,
        ordered_item_data,
        random_uuid
    ):
        url = ordered_item_url(random_uuid)

        res = auth_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

    def test_create_list_ordered_items_fails_with_unauthorized_order_id(
        self,
        user,
        api_client,
        ordered_item_data
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create an order with a different user
        order = SupplierOrderFactory.create()

        # Verify the created order is not linked to the authenticated user
        assert str(order.created_by.id) != str(user.id)

        url = ordered_item_url(order.id)

        res = api_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{order.id}' does not exist."

    def test_create_ordered_item_with_valid_data_id_and_data(
        self,
        auth_client,
        supplier_order,
        ordered_item_data
    ):
        url = ordered_item_url(supplier_order.id)

        res = auth_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 201

        # Verify that ordered item was created
        assert "id" in res.data
        ordered_item = SupplierOrderedItem.objects.filter(id=res.data["id"]).first()
        assert ordered_item is not None

        # Verify that the created ordered item is linked to the correct order
        assert "order" in res.data
        assert str(res.data["order"]) == str(supplier_order.id)
        assert str(ordered_item.order.id) == str(supplier_order.id)

    def test_ordered_item_created_by_authenticated_user(
        self,
        api_client,
        user,
        ordered_item_data,
        supplier_order
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        url = ordered_item_url(supplier_order.id)

        res = api_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 201

        # Verify that the ordered item has been created
        assert "id" in res.data
        ordered_item = SupplierOrderedItem.objects.filter(id=res.data["id"]).first()
        assert ordered_item is not None

        # Verify that the created ordered item is linked to the correct user
        assert "created_by" in res.data
        assert res.data["created_by"] == user.username
        assert str(ordered_item.created_by.id) == str(user.id)

    def test_list_ordered_items_to_authenticated_user(
        self,
        api_client,
        user,
        supplier_order
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create 5 ordered items for the order and authenticated user
        user_items = SupplierOrderedItemFactory.create_batch(
            5,
            order=supplier_order,
            created_by=user,
            supplier=supplier_order.supplier
        )

        # Create 4 ordered items for other orders and users
        SupplierOrderedItemFactory.create_batch(4)

        url = ordered_item_url(supplier_order.id)

        res = api_client.get(url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == len(user_items)

        # Verify that all ordered items belong to the correct order and user
        assert all(
            str(item["order"]) == str(supplier_order.id)
            and item["created_by"] == user.username
            for item in res.data
        )

        user_item_ids = {str(item.id) for item in user_items}
        assert all(
            item["id"] in user_item_ids
            for item in res.data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteSupplierOrderedItemsView:
    """Tests for the get update delete supplier ordered item view"""

    def test_get_update_delete_ordered_items_view_requires_auth(
        self,
        api_client,
        ordered_item
    ):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)
        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_ordered_items_view_allowed_http_methods(
        self,
        auth_client,
        ordered_item,
        ordered_item_2,
        ordered_item_data
    ):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        get_res = auth_client.options(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(url, data=ordered_item_data, format='json')
        print(put_res.data)
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=ordered_item_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_get_update_delete_ordered_item_fails_with_non_existent_order_id(
        self,
        auth_client,
        random_uuid,
        ordered_item,
        ordered_item_data
    ):
        url = ordered_item_url(random_uuid, ordered_item.id)

        res = auth_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

        res = auth_client.put(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

        res = auth_client.delete(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

    def test_get_update_delete_ordered_item_with_unauthorized_order(
        self,
        user,
        api_client,
        ordered_item,
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create another order with a different user
        order = SupplierOrderFactory.create()

        # Verify that the order does not belong to the authenticated user
        assert str(order.created_by.id) != str(user.id)

        url = ordered_item_url(order.id, ordered_item.id)

        res = api_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{order.id}' does not exist."

    def test_get_update_delete_ordered_item_fails_with_non_existent_ordered_item_id(
        self,
        auth_client,
        ordered_item,
        random_uuid,
        ordered_item_data
    ):
        url = ordered_item_url(ordered_item.order.id, random_uuid)

        res = auth_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No SupplierOrderedItem matches the given query."

        res = auth_client.put(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No SupplierOrderedItem matches the given query."

        res = auth_client.delete(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No SupplierOrderedItem matches the given query."

    def test_get_ordered_item_with_valid_id_and_order_id(self, auth_client, ordered_item):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200
    
    def test_ordered_item_response_data_fields(self, auth_client, ordered_item):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()
        
        expected_fields = {
            "id",
            "order",
            "created_by",
            "supplier",
            "item",
            "ordered_quantity",
            "ordered_price",
            "in_inventory",
            "total_price",
            "created_at",
            "updated_at",
        }

        assert expected_fields.issubset(res_data.keys())

    def test_ordered_item_response_data_fields_types(self, auth_client, ordered_item):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert type(res_data["id"]) == str
        assert type(res_data["order"]) == str
        assert type(res_data["created_by"]) == str
        assert type(res_data["supplier"]) == str
        assert type(res_data["item"]) == str
        assert type(res_data["ordered_quantity"]) == int
        assert type(res_data["ordered_price"]) == float
        assert type(res_data["in_inventory"]) == bool
        assert type(res_data["total_price"]) == float
        assert type(res_data["created_at"]) == str
        assert type(res_data["updated_at"]) == str

    def test_ordered_item_response_data_fields_values(self, auth_client, ordered_item):
        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data["id"] == str(ordered_item.id)
        assert res_data["order"] == str(ordered_item.order.id)
        assert res_data["created_by"] == ordered_item.created_by.username
        assert res_data["supplier"] == ordered_item.supplier.name
        assert res_data["item"] == ordered_item.item.name
        assert res_data["ordered_quantity"] == ordered_item.ordered_quantity
        assert res_data["ordered_price"] == float(ordered_item.ordered_price)
        assert res_data["in_inventory"] == ordered_item.in_inventory
        assert res_data["total_price"] == float(ordered_item.total_price)
        assert res_data["created_at"] == date_repr_format(ordered_item.created_at)
        assert res_data["updated_at"] == date_repr_format(ordered_item.updated_at)

    def test_ordered_item_put_update(self, auth_client, ordered_item, ordered_item_data):
        ordered_item_data["ordered_price"] = ordered_item.ordered_price + 100

        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.put(url, data=ordered_item_data, format='json')
        assert res.status_code == 200
        res_data = res.json()

        # Verify that ordered item was updated
        assert "ordered_price" in res_data
        assert res_data["ordered_price"] == float(ordered_item_data["ordered_price"])

        ordered_item.refresh_from_db()
        assert ordered_item.ordered_price == ordered_item_data["ordered_price"]

    def test_ordered_item_patch_update(self, auth_client, ordered_item):
        ordered_item_data = {
            "ordered_price": ordered_item.ordered_price + 100
        }

        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.patch(url, data=ordered_item_data, format='json')
        assert res.status_code == 200
        res_data = res.json()

        # Verify that ordered item was updated
        assert "ordered_price" in res_data
        assert res_data["ordered_price"] == float(ordered_item_data["ordered_price"])

        ordered_item.refresh_from_db()
        assert ordered_item.ordered_price == ordered_item_data["ordered_price"]

    def test_ordered_item_deletion_fails_for_delivered_orders(
        self,
        auth_client,
        ordered_item,
        delivered_status
    ):
        # Update order delivery status to Delivered
        ordered_item.order.delivery_status = delivered_status
        ordered_item.order.save()

        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.delete(url)
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot perform item deletion because the order "
            f"with reference ID '{ordered_item.order.reference_id}' has "
            "already been marked as Delivered. Changes to delivered "
            f"orders' ordered items are restricted to "
            "maintain data integrity."
        )

    def test_ordered_item_deletion_fails_for_single_ordered_item_in_order(
        self,
        auth_client,
        ordered_item
    ):
        # Verify that the ordered item order only has one ordered item
        assert ordered_item.order.ordered_items.count() == 1

        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.delete(url)
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            "This item cannot be deleted because it is the only item in the "
            f"order with reference ID '{ordered_item.order.reference_id}'. "
            f"Every order must have at least one item."
        )

    def test_successful_ordered_item_deletion(
        self,
        auth_client,
        ordered_item,
        ordered_item_2
    ):
        # Verify that the ordered item order has more than one ordered item
        assert ordered_item.order.ordered_items.count() == 2

        # Verify that ordered item order delivery status is not Delivered
        assert ordered_item.order.delivery_status.name != "Delivered"

        url = ordered_item_url(ordered_item.order.id, ordered_item.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the ordered item has been deleted
        assert not SupplierOrderedItem.objects.filter(id=ordered_item.id).exists()


@pytest.mark.django_db
class TestBulkDeleteSupplierOrderedItemsView:
    """Tests for the bulk delete supplier ordered items view."""

    def test_bulk_delete_ordered_items_view_requires_auth(
        self,
        api_client,
        ordered_item
    ):
        url = bulk_delete_items_url(ordered_item.order.id)
        res = api_client.delete(url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_ordered_items_view_allowed_http_methods(
        self,
        auth_client,
        ordered_item,
        ordered_item_2
    ):
        url = bulk_delete_items_url(ordered_item.order.id)

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

        delete_res = auth_client.delete(url, data={"ids": [ordered_item.id]}, format="json")
        assert delete_res.status_code == 200

    def test_bulk_delete_ordered_items_fails_with_nonexistent_order_id(
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
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

    def test_bulk_delete_ordered_items_fails_with_unauthorized_order_id(
        self,
        user,
        api_client
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create an order with a different user
        order = SupplierOrderFactory.create()

        # Verify the created order is not linked to the authenticated user
        assert str(order.created_by.id) != str(user.id)

        url = bulk_delete_items_url(order.id)

        res = api_client.delete(
            url,
            data={"ids": []},
            format="json"
        )
        assert res.status_code == 404

        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{order.id}' does not exist."

    def test_bulk_delete_ordered_items_fails_without_ids_list(
        self,
        auth_client,
        ordered_item
    ):
        url = bulk_delete_items_url(ordered_item.order.id)

        res = auth_client.delete(url, data={}, format="json")
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_ordered_items_fails_with_empty_ids_list(
        self,
        auth_client,
        ordered_item
    ):
        url = bulk_delete_items_url(ordered_item.order.id)

        res = auth_client.delete(url, data={"ids": []}, format="json")
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_ordered_items_fails_with_invalid_uuids(
        self,
        auth_client,
        ordered_item,
    ):
        url = bulk_delete_items_url(ordered_item.order.id)

        res = auth_client.delete(
            url,
            data={"ids": [ordered_item.id, "invalid_uuid_1", "invalid_uuid_2"]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid uuids."

        assert "invalid_uuids" in res_error
        assert len(res_error["invalid_uuids"]) == 2
        assert "invalid_uuid_1" in res_error["invalid_uuids"]
        assert "invalid_uuid_2" in res_error["invalid_uuids"]

    def test_bulk_delete_ordered_items_fails_for_nonexistent_uuids(
        self,
        auth_client,
        ordered_item,
    ):
        random_uuid_1 = str(uuid.uuid4())
        random_uuid_2 = str(uuid.uuid4())

        url = bulk_delete_items_url(ordered_item.order.id)

        res = auth_client.delete(
            url,
            data={"ids": [ordered_item.id, random_uuid_1, random_uuid_2]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not found."

        assert "missing_ids" in res_error
        assert len(res_error["missing_ids"]) == 2
        assert random_uuid_1 in res_error["missing_ids"]
        assert random_uuid_2 in res_error["missing_ids"]

    def test_bulk_delete_ordered_items_fails_for_delivered_orders(
        self,
        auth_client,
        ordered_item,
        ordered_item_2,
        delivered_status
    ):
        # Update ordered item's order status to delivered
        ordered_item.order.delivery_status = delivered_status
        ordered_item.order.save()

        url = bulk_delete_items_url(ordered_item.order.id)

        res = auth_client.delete(
            url,
            data={"ids": [ordered_item.id]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot perform item deletion because the order "
            f"with reference ID '{ordered_item.order.reference_id}' has "
            "already been marked as Delivered. Changes to delivered "
            f"orders' ordered items are restricted to "
            "maintain data integrity."
        )

    def test_bulk_delete_ordered_items_fails_for_all_items_in_order(
        self,
        auth_client,
        supplier_order,
        ordered_item,
        ordered_item_2,
    ):
        # Verify that both ordered items belong to the specified order
        assert str(ordered_item.order.id) == str(supplier_order.id)
        assert str(ordered_item_2.order.id) == str(supplier_order.id)

        # Verify that the order only has the two ordered items
        assert supplier_order.ordered_items.count() == 2

        url = bulk_delete_items_url(supplier_order.id)

        # Try to delete both ordered items
        res = auth_client.delete(
            url,
            data={"ids": [ordered_item.id, ordered_item_2.id]},
            format="json"
        )
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Cannot delete items from order with reference ID "
            f"'{supplier_order.reference_id}' as it would leave no items linked. "
            f"Each order must have at least one item."
        )

    def test_bulk_delete_ordered_items_succeeds(
        self,
        auth_client,
        supplier_order,
        ordered_item,
        ordered_item_2,
    ):
        # Verify that both ordered items belong to the specified order
        assert str(ordered_item.order.id) == str(supplier_order.id)
        assert str(ordered_item_2.order.id) == str(supplier_order.id)

        # Create a third ordered item to prevent order with no items linked error
        ordered_item_3 = SupplierOrderedItemFactory.create(
            supplier=supplier_order.supplier,
            created_by=supplier_order.created_by,
            order=supplier_order
        )

        # Verify that the order has three ordered items
        assert supplier_order.ordered_items.count() == 3

        url = bulk_delete_items_url(supplier_order.id)

        # Try to delete two ordered items
        res = auth_client.delete(
            url,
            data={"ids": [ordered_item.id, ordered_item_2.id]},
            format="json"
        )
        assert res.status_code == 200

        assert "message" in res.data
        assert res.data["message"] == "2 ordered items successfully deleted."

        # Verify that the two deleted ordered items were deleted
        assert not SupplierOrderedItem.objects.filter(
            id__in=[ordered_item.id, ordered_item_2.id]
        ).exists()

        # Verify that the third ordered item was not deleted
        assert SupplierOrderedItem.objects.filter(
            id=ordered_item_3.id
        ).exists()

        # Verify that the order still has one ordered item
        supplier_order.refresh_from_db()
        assert supplier_order.ordered_items.count() == 1


@pytest.mark.django_db
class TestGetSupplierOrdersDataView:
    """Tests for the get supplier orders data view."""

    def test_get_supplier_orders_view_requires_auth(
        self,
        api_client,
        supplier_orders_data_url
    ):
        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_supplier_orders_view_allowed_http_methods(
        self,
        auth_client,
        supplier_orders_data_url
    ):
        get_res = auth_client.get(supplier_orders_data_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(supplier_orders_data_url)
        assert post_res.status_code == 405
        assert "detail" in post_res.data
        assert post_res.data["detail"] == "Method \"POST\" not allowed."

        put_res = auth_client.put(supplier_orders_data_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(supplier_orders_data_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(supplier_orders_data_url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_get_supplier_orders_response_data_fields(
        self,
        auth_client,
        supplier_orders_data_url,
    ):
        res = auth_client.get(supplier_orders_data_url)
        assert res.status_code == 200

        expected_fields = {
            "suppliers",
            "no_supplier_items",
            "suppliers_count",
            "orders_count",
            "order_status"
        }

        assert expected_fields.issubset(res.data.keys())

    def test_get_supplier_orders_response_data_fields_types(
        self,
        auth_client,
        supplier_orders_data_url,
    ):
        res = auth_client.get(supplier_orders_data_url)
        assert res.status_code == 200
        res_data = res.json()

        assert isinstance(res_data["suppliers"], list)
        assert isinstance(res_data["no_supplier_items"], list)
        assert isinstance(res_data["suppliers_count"], int)
        assert isinstance(res_data["orders_count"], int)
        assert isinstance(res_data["order_status"], dict)

    def test_get_supplier_orders_data_suppliers_field_structure_and_value(
        self,
        user,
        api_client,
        supplier_orders_data_url,
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create two suppliers for the authenticated user
        supplier_1 = SupplierFactory.create(name="Supplier 1", created_by=user)
        supplier_2 = SupplierFactory.create(name="Supplier 2", created_by=user)

        # Create two items for each supplier
        item_1 = ItemFactory.create(name="Item 1", supplier=supplier_1)
        item_2 = ItemFactory.create(name="Item 2", supplier=supplier_1)
        item_3 = ItemFactory.create(name="Item 3", supplier=supplier_2)
        item_4 = ItemFactory.create(name="Item 4", supplier=supplier_2)

        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 200

        assert "suppliers" in res.data
        res_data = res.json()
        suppliers = res_data["suppliers"]
        assert isinstance(suppliers, list)
        assert len(suppliers) == 2

        # Verify that suppliers has a list of dictionaries
        assert all(isinstance(supplier, dict) for supplier in suppliers)

        # Verify that each supplier object contains the supplier name and items
        assert all("name" in supplier for supplier in suppliers)
        assert all("item_names" in supplier for supplier in suppliers)

        # Verify that the supplier name is correct
        res_supplier_names = [supplier["name"] for supplier in suppliers]
        assert supplier_1.name in res_supplier_names
        assert supplier_2.name in res_supplier_names

        # Verify that the items length and names are correct
        assert len(suppliers[0]["item_names"]) == 2
        assert len(suppliers[1]["item_names"]) == 2

        for supplier in suppliers:
            assert isinstance(supplier["item_names"], list)
            if supplier["name"] == supplier_1.name:
                assert item_1.name in supplier["item_names"]
                assert item_2.name in supplier["item_names"]
            elif supplier["name"] == supplier_2.name:
                assert item_3.name in supplier["item_names"]
                assert item_4.name in supplier["item_names"]

    def test_get_supplier_orders_data_no_supplier_items_field_structure_and_value(
        self,
        user,
        api_client,
        supplier,
        supplier_orders_data_url,
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create two items without suppliers fo the authenticated user
        item_1 = ItemFactory.create(name="item 1", created_by=user, supplier=None)
        item_2 = ItemFactory.create(name="item 2", created_by=user, supplier=None)

        # Create one item with supplier for the authenticated user
        item_3 = ItemFactory.create(name="item 3", supplier=supplier, created_by=user)      

        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 200

        assert "no_supplier_items" in res.data
        res_data = res.json()

        no_supplier_items = res_data["no_supplier_items"]
        
        assert isinstance(no_supplier_items, list)
        assert len(no_supplier_items) == 2

        # Verify that no_supplier_items only includes the items without supplier
        assert item_1.name in no_supplier_items
        assert item_2.name in no_supplier_items
        assert item_3.name not in no_supplier_items

    def test_get_supplier_orders_data_suppliers_count_field_structure_and_value(
        self,
        user,
        api_client,
        supplier_orders_data_url
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create two suppliers for the authenticated user
        SupplierFactory.create_batch(2, created_by=user)

        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 200

        assert "suppliers_count" in res.data
        res_data = res.json()
        assert isinstance(res_data["suppliers_count"], int)
        assert res_data["suppliers_count"] == 2

    def test_get_supplier_orders_data_orders_count_field_structure_and_value(
        self,
        user,
        api_client,
        supplier_orders_data_url
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create five supplier orders for the authenticated user
        SupplierOrderFactory.create_batch(5, created_by=user)

        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 200

        assert "orders_count" in res.data
        res_data = res.json()
        assert isinstance(res_data["orders_count"], int)
        assert res_data["orders_count"] == 5

        assert res_data["orders_count"] == (
            SupplierOrder.objects.filter(created_by=user).count()
        )

    def test_get_client_orders_data_order_status_field_structure_and_value(
        self,
        user,
        api_client,
        supplier_orders_data_url
    ):
        # Authenticate the api client to the given user
        api_client.force_authenticate(user=user)

        # Create 2 supplier orders for the auth user
        # with an active status as delivery status
        active_status = OrderStatusFactory.create(
            name=random.choice(ACTIVE_DELIVERY_STATUS)
        )
        active_orders = SupplierOrderFactory.create_batch(
            2,
            created_by=user,
            delivery_status=active_status
        )

        # Create 3 supplier orders for the auth user
        # with an completed status as delivery status
        completed_status = OrderStatusFactory.create(
            name=random.choice(COMPLETED_STATUS)
        )
        completed_orders = SupplierOrderFactory.create_batch(
            3,
            created_by=user,
            delivery_status=completed_status
        )

        # Create 4 supplier orders for the auth user
        # with a failed status as delivery status
        failed_status = OrderStatusFactory.create(
            name=random.choice(FAILED_STATUS)
        )
        failed_orders = SupplierOrderFactory.create_batch(
            4,
            created_by=user,
            delivery_status=failed_status
        )

        res = api_client.get(supplier_orders_data_url)
        assert res.status_code == 200
        res_data = res.json()
        assert isinstance(res_data, dict)

        assert "order_status" in res_data
        order_status = res_data["order_status"]
        
        # Delivery status field
        assert "delivery_status" in order_status
        assert order_status["delivery_status"] == DELIVERY_STATUS_OPTIONS

        # Payment status field
        assert "payment_status" in order_status
        assert order_status["payment_status"] == PAYMENT_STATUS_OPTIONS

        # Active orders field
        assert "active" in order_status
        assert order_status["active"] == len(active_orders)

        # Completed orders field
        assert "completed" in order_status
        assert order_status["completed"] == len(completed_orders)

        # Failed orders field
        assert "failed" in order_status
        assert order_status["failed"] == len(failed_orders)
