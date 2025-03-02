import pytest
import jwt
from django.conf import settings
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
from apps.base.models import User
from apps.inventory.models import Item
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import (
    CategoryFactory,
    VariantFactory,
    VariantOptionFactory,
    ItemFactory
)


@pytest.fixture
def create_list_item_url():
    return reverse('create_list_items')


@pytest.mark.django_db
class TestCreateListItemsView:
    """Tests for the CreateListItems View"""

    def test_create_list_items_view_requires_authentication(
        self,
        api_client,
        create_list_item_url
    ):
        res = api_client.get(create_list_item_url)
        
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_items_view_allowed_http_methods(
        self,
        auth_client,
        item_data,
        create_list_item_url
    ):
        get_res = auth_client.get(create_list_item_url)
        assert get_res.status_code == 200
        
        post_res = auth_client.post(
            create_list_item_url,
            data=item_data,
            format='multipart'
        )
        assert post_res.status_code == 201
    
        put_res = auth_client.put(
            create_list_item_url,
            data=item_data,
            format='multipart'
        )
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'
    
        delete_res = auth_client.delete(create_list_item_url)
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

    def test_create_item_with_valid_data(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 201
        assert "id" in res.data

        item_id = res.data["id"]
        assert Item.objects.filter(id=item_id).exists()

    def test_create_item_fails_without_name(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        item_data.pop('name')

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"] == ["This field is required."]
    
    def test_create_item_fails_with_exiting_name(
        self,
        auth_client,
        create_list_item_url,
        user,
        item_data
    ):
        ItemFactory.create(created_by=user, name="Projector")

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"] == ["Item with this name already exists."]
    
    def test_create_item_fails_without_quantity(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        item_data.pop('quantity')

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "quantity" in res.data
        assert res.data["quantity"] == ["This field is required."]
    
    def test_create_item_fails_with_negative_quantity(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        item_data["quantity"] = -2

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "quantity" in res.data
        assert (
            res.data["quantity"] ==
            ["Ensure this value is greater than or equal to 0."]
        )
    
    def test_create_item_fails_without_price(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        item_data.pop('price')

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "price" in res.data
        assert res.data["price"] == ["This field is required."]

    def test_create_item_fails_with_negative_price(
        self,
        auth_client,
        create_list_item_url,
        item_data
    ):
        item_data["price"] = -22
        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "price" in res.data
        assert (
            res.data["price"] ==
            ["Ensure this value is greater than or equal to 0.0."]
        )

    def test_item_creation_created_by_is_the_request_user(
        self,
        auth_client,
        access_token,
        create_list_item_url,
        item_data
    ):
        token_payload = AccessToken(access_token)
        token_user_id = token_payload["user_id"]

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )

        assert res.status_code == 201
        assert "created_by" in res.data
        
        item_created_by = User.objects.get(username=res.data["created_by"])
        assert str(item_created_by.id) == str(token_user_id)
