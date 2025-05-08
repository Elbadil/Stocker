import pytest
from django.urls import reverse
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
