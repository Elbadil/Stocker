import pytest
from django.urls import reverse
from apps.base.models import Activity
from apps.supplier_orders.models import Supplier
from apps.supplier_orders.factories import (
    SupplierFactory,
    SupplierOrderedItemFactory,
    SupplierOrderFactory
)
from utils.serializers import date_repr_format, get_location

@pytest.fixture
def create_list_supplier_url():
    return reverse('create_list_suppliers')

def supplier_url(supplier_id: str):
    return reverse('get_update_delete_suppliers', kwargs={"id": supplier_id})


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
