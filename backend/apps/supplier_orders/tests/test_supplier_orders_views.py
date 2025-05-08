import pytest
import uuid
from django.urls import reverse
from apps.base.models import Activity
from apps.supplier_orders.models import Supplier, SupplierOrder
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderedItemFactory,
    SupplierOrderFactory
)
from utils.serializers import date_repr_format, get_location

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

    def test_supplier__operations_fail_with_inexistent_id(self, auth_client, random_uuid):
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
