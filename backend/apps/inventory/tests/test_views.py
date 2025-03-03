import pytest
import json
from dateutil import parser
from datetime import datetime, timezone, timedelta
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

        assert "name" in res.data
        assert res.data["name"] == "Projector"

        assert "quantity" in res.data
        assert res.data["quantity"] == 2

        assert "price" in res.data
        assert res.data["price"] == 199.99

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

    def test_create_item_with_picture_file_field(
        self,
        auth_client,
        create_list_item_url,
        item_data,
        setup_cleanup_picture
    ):
        picture = setup_cleanup_picture
        item_data["picture"] = picture

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )
        assert res.status_code == 201
        assert "picture" in res.data
        assert res.data["picture"].endswith(picture.name)

    def test_item_response_data_fields(
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
        assert "created_by" in res.data
        assert "supplier" in res.data
        assert "category" in res.data
        assert "name" in res.data
        assert "quantity" in res.data
        assert "price" in res.data
        assert "total_price" in res.data
        assert "picture" in res.data
        assert "variants" in res.data
        assert "total_client_orders" in res.data
        assert 'total_supplier_orders' in res.data
        assert "in_inventory" in res.data
        assert "updated" in res.data
        assert "created_at" in res.data
        assert "updated_at" in res.data
    
    def test_item_response_data_for_basic_fields(
        self,
        auth_client,
        create_list_item_url,
        category,
        supplier,
        user,
    ):
        item_data = {
            "category": category.name,
            "supplier": supplier.name,
            "name": "Projector",
            "quantity": 2,
            "price": 199.99,
        }
    
        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )
        assert res.status_code == 201

        expected_data = {
            "created_by": user.username,
            "category": category.name,
            "supplier": supplier.name,
            "name": "Projector",
            "quantity": 2,
            "price": 199.99,
            "total_price": item_data["quantity"] * item_data["price"],
        }

        assert "id" in res.data
        item = Item.objects.get(id=res.data["id"])
        assert item is not None

        assert str(res.data["id"]) == str(item.id)
        assert res.data["created_by"] == expected_data['created_by']
        assert res.data["supplier"] == expected_data['supplier']
        assert res.data["category"] == expected_data['category']
        assert res.data["name"] == expected_data['name']
        assert res.data["quantity"] == expected_data['quantity']
        assert res.data["price"] == expected_data['price']
        assert res.data["total_price"] == expected_data["total_price"]

    def test_item_response_data_for_picture_field(
        self,
        auth_client,
        create_list_item_url,
        item_data,
        setup_cleanup_picture
    ):
        picture = setup_cleanup_picture
        item_data["picture"] = picture
        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )
        assert res.status_code == 201
        assert "picture" in res.data
        assert res.data["picture"].endswith(picture.name)

    def test_item_response_data_for_variants_field(
        self,
        auth_client,
        create_list_item_url,
        item_data,
    ):
        variants = [
            {
                "name": "Color",
                "options": ["red", "blue"]
            },
            {
                "name": "Size",
                "options": ["160kg", "90kg"]
            },
        ]
        item_data["variants"] = json.dumps(variants)

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )
        assert res.status_code == 201
        assert "variants" in res.data
        assert res.data["variants"] == variants

    def test_item_response_data_for_date_fields(
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
        item = Item.objects.get(id=res.data["id"])
        assert item is not None

        assert "created_at" in res.data
        assert "updated_at" in res.data

        assert res.data["created_at"] == item.created_at.strftime('%d/%m/%Y')
        assert res.data["updated_at"] == item.updated_at.strftime('%d/%m/%Y')

    def test_item_response_data_for_boolean_fields(
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
        assert "in_inventory" in res.data
        assert "updated" in res.data

        assert res.data["in_inventory"] == True
        assert res.data["updated"] == False

    def test_list_items_response_data_structure(
        self,
        auth_client,
        create_list_item_url
    ):
        res = auth_client.get(create_list_item_url)
        assert res.status_code == 200
        assert isinstance(res.data, list)
    
    def test_list_items_response_data_objects_structure(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        ItemFactory.create_batch(10, created_by=user)
        res = auth_client.get(create_list_item_url)

        assert res.status_code == 200
        assert len(res.data) == 10

        item_1 = res.data[0]

        assert type(item_1) == dict
    
    def test_list_items_response_data_objects_data_fields(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        ItemFactory.create_batch(10, created_by=user)
        res = auth_client.get(create_list_item_url)

        assert res.status_code == 200
        assert len(res.data) == 10

        item_1 = res.data[0]

        assert type(item_1) == dict

        assert "id" in item_1
        assert "created_by" in item_1
        assert "supplier" in item_1
        assert "category" in item_1
        assert "name" in item_1
        assert "quantity" in item_1
        assert "price" in item_1
        assert "total_price" in item_1
        assert "picture" in item_1
        assert "variants" in item_1
        assert "total_client_orders" in item_1
        assert 'total_supplier_orders' in item_1
        assert "in_inventory" in item_1
        assert "updated" in item_1
        assert "created_at" in item_1
        assert "updated_at" in item_1

    def test_items_sorted_desc_by_created_at(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        # Create 10 item entries
        items = ItemFactory.create_batch(10, created_by=user)

        # Assign unique dates manually
        now = datetime.now(timezone.utc)
        for i, item in enumerate(items):
            item.created_at = now + timedelta(days=i)

        # Perform bulk update to save changes
        Item.objects.bulk_update(items, ['created_at'])

        res = auth_client.get(create_list_item_url)

        assert res.status_code == 200
        assert len(res.data) == 10
        res_items = res.data

        sorted_items = sorted(
            res_items,
            key=lambda x: parser.parse(x['created_at']), reverse=True
        )

        assert res_items == sorted_items

    def test_list_items_with_in_inventory_query_set_to_true(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        in_inventory_items = ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )
        item_not_in_inventory = ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        items = Item.objects.all()
        assert len(items) == 10

        res = auth_client.get(f'{create_list_item_url}?in_inventory=true')
        assert res.status_code == 200
        assert len(res.data) == 9
    
    def test_list_items_with_in_inventory_query_set_to_false(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        in_inventory_items = ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )
        item_not_in_inventory = ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        items = Item.objects.all()
        assert len(items) == 10

        res = auth_client.get(f'{create_list_item_url}?in_inventory=false')
        assert res.status_code == 200
        assert len(res.data) == 10
    
    def test_list_items_without_in_inventory_query_param(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        in_inventory_items = ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )
        item_not_in_inventory = ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        items = Item.objects.all()
        assert len(items) == 10

        res = auth_client.get(create_list_item_url)
        assert res.status_code == 200
        assert len(res.data) == 10
