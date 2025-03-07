import pytest
import json
import uuid
from decimal import Decimal
from django.db.models import CharField
from django.db.models.functions import Cast
from datetime import datetime, timezone, timedelta
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
from apps.base.models import User, Activity
from apps.inventory.models import Item, VariantOption
from apps.inventory.serializers import ItemSerializer
from apps.inventory.factories import (
    CategoryFactory,
    VariantFactory,
    VariantOptionFactory,
    ItemFactory
)
from apps.supplier_orders.factories import SupplierFactory
from apps.base.factories import UserFactory


@pytest.fixture
def create_list_item_url():
    return reverse('create_list_items')

@pytest.fixture
def bulk_delete_items_url():
    return reverse('bulk_delete_items')

@pytest.fixture
def get_inventory_data_url():
    return reverse('get_inventory_data')

def item_url(item):
    """
    Generates the URL for retrieving, updating, or deleting an item.
    """
    return reverse('get_update_delete_items', kwargs={'id': item.id})


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
        color_variant = {
            "name": "Color",
            "options": ["red", "blue"]
        }
        size_variant = {
            "name": "Size",
            "options": ["160kg", "90kg"]
        }

        variants = [color_variant, size_variant]
        item_data["variants"] = json.dumps(variants)

        res = auth_client.post(
            create_list_item_url,
            item_data,
            format='multipart'
        )
        assert res.status_code == 201
        assert "variants" in res.data
        assert isinstance(res.data["variants"], list)
        res_variants = res.data["variants"]
        assert len(res_variants) == 2

        assert color_variant in res_variants
        assert size_variant in res_variants

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
    
    def test_list_items_to_authenticated_user(
        self, 
        api_client,
        access_token,
        user,
        create_list_item_url
    ):
        ItemFactory.create_batch(10, created_by=user)

        token_payload = AccessToken(access_token)
        token_payload["user_id"] == user.id

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        res = api_client.get(create_list_item_url)
        assert res.status_code == 200
        assert len(res.data) == 10

        assert all(item["created_by"] == user.username for item in res.data)

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
            item.created_at = now + timedelta(seconds=i)

        # Perform bulk update to save changes
        Item.objects.bulk_update(items, ['created_at'])
        sorted_items_ids = (
            Item.objects.order_by('-created_at')
            .annotate(id_str=Cast('id', CharField()))
            .values_list('id_str', flat=True)
        )

        res = auth_client.get(create_list_item_url)

        assert res.status_code == 200
        assert len(res.data) == 10
        response_items_ids = [item['id'] for item in res.data]

        assert response_items_ids == list(sorted_items_ids)
    
    def test_list_items_with_zero_registered_items(
        self,
        auth_client,
        create_list_item_url
    ):
        res = auth_client.get(create_list_item_url)

        assert res.status_code == 200
        assert isinstance(res.data, list)
        assert len(res.data) == 0

    def test_list_items_with_in_inventory_query_set_to_true(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        # Create 9 items in inventory
        ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )

        # Create 1 item with in_inventory attribute set to False
        ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        res = auth_client.get(f'{create_list_item_url}?in_inventory=true')
        assert res.status_code == 200
        assert len(res.data) == 9

    def test_list_items_with_in_inventory_query_set_to_false(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        # Create 9 items in inventory
        ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )

        # Create 1 item with in_inventory attribute set to False
        ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        res = auth_client.get(f'{create_list_item_url}?in_inventory=false')
        assert res.status_code == 200
        assert len(res.data) == 10
    
    def test_list_all_items_by_default(
        self,
        auth_client,
        user,
        create_list_item_url
    ):
        # Create 9 items in inventory
        ItemFactory.create_batch(
            9,
            created_by=user,
            in_inventory=True
        )

        # Create 1 item with in_inventory attribute set to False
        ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        res = auth_client.get(create_list_item_url)
        assert res.status_code == 200
        assert len(res.data) == 10


@pytest.mark.django_db
class TestGetUpdateDeleteItemsView:
    """Tests for the GetUpdateDeleteItems View"""

    def test_get_update_delete_item_view_requires_authentication(
        self,
        api_client,
        item
    ):
        url = item_url(item)

        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_item_view_allowed_http_methods(
        self,
        auth_client,
        item,
        item_data
    ):
        url = item_url(item)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200
        
        post_res = auth_client.post(
            url,
            data=item_data,
            format='multipart'
        )
        assert post_res.status_code == 405
        assert post_res.data["detail"] == 'Method \"POST\" not allowed.'

        put_res = auth_client.put(
            url,
            data=item_data,
            format='multipart'
        )
        assert put_res.status_code == 200
    
        patch_res = auth_client.patch(
            url,
            data=item_data,
            format='multipart'
        )
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_get_item_with_valid_item(self, auth_client, user, item_data):
        item = ItemFactory.create(created_by=user, **item_data)
        url = item_url(item)

        res = auth_client.get(url)
        assert res.status_code == 200

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
    
    def test_get_item_with_inexistent_item_id(self, auth_client, random_uuid):
        url = reverse('get_update_delete_items', kwargs={'id': random_uuid})

        res = auth_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No Item matches the given query."

    def test_get_item_not_linked_to_authenticated_user(
        self,
        auth_client,
        access_token,
        item_data
    ):
        item = ItemFactory.create(**item_data)

        token_payload = AccessToken(access_token)
        assert item.created_by.id != token_payload["user_id"]

        url = item_url(item)

        res = auth_client.get(url)
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No Item matches the given query."

    def test_update_item_with_valid_data(self, auth_client, user, category, item_data):
        item_data["created_by"] = user
        item_data["category"] = category
        item = ItemFactory.create(**item_data)
        
        new_item_data = {
            "name": "Pack",
            "quantity": 4,
            "price": 299.50
        }

        url = item_url(item)

        res = auth_client.put(
            url,
            data=new_item_data,
            format='multipart'
        )
        assert res.status_code == 200

        item_update = res.data

        # Verify that specified fields in request data have changed
        assert (
            item_update["name"] == new_item_data["name"]
            and item_update["name"] != item.name
        )
        assert (
            item_update["quantity"] == new_item_data["quantity"]
            and item_update["quantity"] != item.quantity
        )
        assert (
            item_update["price"] == new_item_data["price"]
            and item_update["price"] != item.price
        )
        # Verify that other item fields remained unchanged
        assert item_update["created_by"] == item.created_by.username
        assert item_update["category"] == item.category.name

    def test_partial_update_item(self, auth_client, user, item_data):
        item = ItemFactory.create(created_by=user, **item_data)

        url = item_url(item)

        res = auth_client.patch(
            url,
            data={"name": "Pack"},
            format='multipart'
        )
        assert res.status_code == 200

        item_update = res.data

        # Verify that item's name has changed
        assert (
            item_update["name"] == "Pack"
            and item_update["name"] != item.name
        )
        # Verify that other item fields remained unchanged
        assert item_update["quantity"] == item.quantity
        assert item_update["price"] == item.price

    def test_item_update_removes_optional_field_if_set_to_null(
        self,
        auth_client,
        user,
        supplier
    ):
        item = ItemFactory.create(created_by=user, supplier=supplier)
        assert item.supplier is not None

        url = item_url(item)

        res = auth_client.patch(
            url,
            data={"supplier": "null"},
            format='multipart'
        )
        assert res.status_code == 200

        item_update = res.data
        assert item_update["supplier"] == None

    def test_update_item_with_inexistent_item_id(
        self,
        auth_client,
        random_uuid,
        item_data,
    ):
        url = reverse('get_update_delete_items', kwargs={'id': random_uuid})

        res = auth_client.put(
            url,
            data=item_data,
            format='multipart'
        )
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No Item matches the given query."

    def test_update_item_not_linked_to_authenticated_user(
        self,
        auth_client,
        access_token,
        item_data,
    ):
        item = ItemFactory.create(**item_data)

        token_payload = AccessToken(access_token)
        assert item.created_by.id != token_payload["user_id"]

        url = item_url(item)

        new_item_data = {
            "name": "Pack",
            "quantity": 4,
            "price": 299.50
        }

        res = auth_client.put(
            url,
            data=new_item_data,
            format='multipart'
        )
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == "No Item matches the given query."
    
    def test_delete_item_with_valid_item_id(self, auth_client, user):
        item = ItemFactory.create(created_by=user)
        assert Item.objects.filter(id=item.id).exists()

        url = item_url(item)

        res = auth_client.delete(url)
        assert res.status_code == 204
        assert not Item.objects.filter(id=item.id).exists()

    def test_delete_item_with_inexistent_id(self, auth_client, random_uuid):
        url = reverse('get_update_delete_items', kwargs={'id': random_uuid})

        res = auth_client.delete(url)
        assert res.status_code == 404
        assert res.data["detail"] == "No Item matches the given query."

    def test_delete_item_not_linked_to_authenticated_user(
        self,
        auth_client,
        access_token
    ):
        item = ItemFactory.create()

        token_payload = AccessToken(access_token)
        assert item.created_by.id != token_payload["user_id"]

        url = item_url(item)

        res = auth_client.delete(url)
        assert res.status_code == 404
        assert res.data["detail"] == "No Item matches the given query."
    
    def test_item_deletion_deletes_linked_variant_option_instances(
        self,
        auth_client,
        item_data,
        user
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
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert VariantOption.objects.filter(item=item).exists()

        url = item_url(item)

        res = auth_client.delete(url)
        assert res.status_code == 204
        assert not Item.objects.filter(id=item.id).exists()
        assert not VariantOption.objects.filter(item=item).exists()

    def test_item_deletion_registers_a_new_activity(self, auth_client, user, item_data):
        item = ItemFactory.create(created_by=user, **item_data)
        assert Item.objects.filter(id=item.id).exists()

        url = item_url(item)

        res = auth_client.delete(url)
        assert res.status_code == 204
        assert not Item.objects.filter(id=item.id).exists()

        assert (
            Activity.objects.filter(
                action="deleted",
                model_name="item",
                object_ref__contains=[item_data["name"]]
            ).exists()
        )


@pytest.mark.django_db
class TestBulkDeleteItemsView:
    """Tests for the BulkDeleteItems View"""

    def test_bulk_delete_items_requires_authentication(
        self,
        api_client,
        bulk_delete_items_url
    ):
        res = api_client.delete(bulk_delete_items_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_items_allowed_http_methods(
        self,
        auth_client,
        user,
        bulk_delete_items_url
    ):
        items = ItemFactory.create_batch(3, created_by=user)
        item_ids = [item.id for item in items]

        get_res = auth_client.get(bulk_delete_items_url, data={"ids": item_ids})
        assert get_res.status_code == 405
        assert get_res.data["detail"] == 'Method \"GET\" not allowed.'
        
        post_res = auth_client.post(bulk_delete_items_url, data={"ids": item_ids})
        assert post_res.status_code == 405
        assert post_res.data["detail"] == 'Method \"POST\" not allowed.'
    
        put_res = auth_client.put(bulk_delete_items_url)
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'

        delete_res = auth_client.delete(
            bulk_delete_items_url,
            data={"ids": item_ids},
            format='json'
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_items_with_valid_item_ids(
        self,
        auth_client,
        bulk_delete_items_url,
        user
    ):
        items = ItemFactory.create_batch(3, created_by=user)
        item_ids = [item.id for item in items]

        res = auth_client.delete(
            bulk_delete_items_url,
            data={"ids": item_ids},
            format='json'
        )
        assert res.status_code == 200
        assert not Item.objects.filter(id__in=item_ids).exists()

        assert "message" in res.data
        assert res.data["message"] == "3 items successfully deleted."

    def test_bulk_delete_items_without_ids_in_request_data(
        self,
        auth_client,
        bulk_delete_items_url
    ):
        res = auth_client.delete(bulk_delete_items_url)

        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."
    
    def test_bulk_delete_items_fails_with_invalid_uuids(
        self,
        auth_client,
        bulk_delete_items_url,
        user
    ):
        item = ItemFactory.create(created_by=user)
        invalid_uuid_1 = "invalid-uuid-1"
        invalid_uuid_2 = "invalid-uuid-2"
        ids = [item.id, invalid_uuid_1, invalid_uuid_2]

        res = auth_client.delete(
            bulk_delete_items_url,
            data={"ids": ids},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert (
            res_error["message"] ==
            "Some or all provided IDs are not valid UUIDs."
        )

        assert "invalid_ids" in res_error
        invalid_ids = res_error["invalid_ids"]
        assert len(invalid_ids) == 2
        assert invalid_uuid_1 in invalid_ids
        assert invalid_uuid_2 in invalid_ids
    
    def test_bulk_delete_items_fails_with_inexistent_item_ids(
        self,
        auth_client,
        bulk_delete_items_url,
        user
    ):
        item = ItemFactory.create(created_by=user)
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        ids = [item.id, random_id_1, random_id_2]

        res = auth_client.delete(
            bulk_delete_items_url,
            data={"ids": ids},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert (
            res_error["message"] ==
            "Some or all items could not be found."
        )

        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == 2
        assert random_id_1 in missing_ids
        assert random_id_2 in missing_ids

    def test_bulk_delete_fails_with_unauthorized_items(
        self,
        auth_client,
        user,
        bulk_delete_items_url
    ):
        user_items = ItemFactory.create_batch(2, created_by=user)
        other_items = ItemFactory.create_batch(3)

        item_ids = [item.id for item in user_items + other_items]

        res = auth_client.delete(
            bulk_delete_items_url,
            data={"ids": item_ids},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert (
            res_error["message"] ==
            "Some or all items could not be found."
        )
        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == len(other_items)


@pytest.mark.django_db
class TestGetInventoryDataView:
    """Tests for GetInventoryData View"""

    def test_inventory_data_view_requires_authentication(
        self,
        api_client,
        get_inventory_data_url
    ):
        res = api_client.get(get_inventory_data_url)

        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_inventory_data_view_allowed_http_methods(
        self,
        auth_client,
        get_inventory_data_url
    ):
        get_res = auth_client.get(get_inventory_data_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(get_inventory_data_url)
        assert post_res.status_code == 405
        assert post_res.data["detail"] == 'Method \"POST\" not allowed.'

        put_res = auth_client.put(get_inventory_data_url)
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'
    
        delete_res = auth_client.delete(get_inventory_data_url)
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

    def test_inventory_data_response_fields(
        self,
        auth_client,
        get_inventory_data_url
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        expected_fields = {
            "items",
            "total_items",
            "total_value",
            "total_quantity",
            "categories",
            "suppliers",
            "variants"
        }

        assert expected_fields.issubset(res.data.keys())

    def test_inventory_data_response_fields_types(
        self,
        auth_client,
        get_inventory_data_url
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert isinstance(res.data["items"], list)
        assert type(res.data["total_items"]) == int
        assert type(res.data["total_value"]) == int
        assert type(res.data["total_quantity"]) == int
        assert type(res.data["categories"]) == dict
        assert type(res.data["suppliers"]) == dict
        assert isinstance(res.data["variants"], list)

    def test_inventory_data_items_field(
        self,
        auth_client,
        get_inventory_data_url,
        user,
    ):
        item_data = {
            "created_by": user,
            "in_inventory": True
        }

        item_1 = ItemFactory.create(name="Projector", quantity=3, **item_data)
        item_2 = ItemFactory.create(name="Pack", quantity=5, **item_data)

        item_1_data = {
            "name": item_1.name,
            "quantity": item_1.quantity
        }

        item_2_data = {
            "name": item_2.name,
            "quantity": item_2.quantity
        }

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "items" in res.data
        res_items = res.data["items"]
        assert isinstance(res_items, list)
        assert len(res_items) == 2

        # Items objects structure
        res_item_1 = res_items[0]
        assert type(res_item_1) == dict
        assert "name" in res_item_1
        assert "quantity" in res_item_1

        # Ensure created items in response's items list
        assert item_1_data in res_items
        assert item_2_data in res_items

    def test_inventory_data_total_fields(
        self,
        auth_client,
        get_inventory_data_url,
        user,
    ):
        item_data = {
            "created_by": user,
            "in_inventory": True
        }

        item_1 = ItemFactory.create(quantity=3, price=299, **item_data)
        item_2 = ItemFactory.create(quantity=5, price=150, **item_data)
        item_3 = ItemFactory.create(quantity=1, price=79, **item_data)

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "total_items" in res.data
        assert type(res.data["total_items"]) == int
        assert res.data["total_items"] == 3

        assert "total_quantity" in res.data
        assert type(res.data["total_quantity"]) == int
        assert res.data["total_quantity"] == sum([
            item_1.quantity,
            item_2.quantity,
            item_3.quantity
        ])

        assert "total_value" in res.data
        assert type(res.data["total_value"]) == Decimal
        assert res.data["total_value"] == sum([
            item_1.total_price,
            item_2.total_price,
            item_3.total_price
        ])
    
    def test_inventory_data_filters_items_in_inventory(
        self,
        auth_client,
        get_inventory_data_url,
        user,
    ):
        # Create 4 items in inventory
        ItemFactory.create_batch(
            4,
            created_by=user,
            in_inventory=True
        )

        # Create 1 item with in_inventory attribute set to False
        ItemFactory.create(
            created_by=user,
            in_inventory=False
        )

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "items" in res.data
        res_items = res.data["items"]
        assert isinstance(res_items, list)
        assert len(res_items) == 4

    def test_inventory_data_with_no_registered_items(
        self,
        auth_client,
        get_inventory_data_url,
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "items" in res.data
        res_items = res.data["items"]
        assert isinstance(res_items, list)
        assert len(res_items) == 0

        assert "total_items" in res.data
        assert res.data["total_items"] == 0

        assert "total_quantity" in res.data
        assert res.data["total_quantity"] == 0

        assert "total_value" in res.data
        assert res.data["total_value"] == 0

    def test_inventory_data_categories_field(
        self,
        auth_client,
        get_inventory_data_url,
        user
    ):
        categories = CategoryFactory.create_batch(3, created_by=user)

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "categories" in res.data
        res_categories = res.data["categories"]
        assert type(res_categories) == dict

        assert "count" in res_categories
        assert type(res_categories["count"]) == int
        assert res_categories["count"] == len(categories)

        assert "names" in res_categories
        assert isinstance(res_categories["names"], list)
        assert all(
            category.name in res_categories["names"]
            for category in categories
        )

    def test_inventory_data_with_no_registered_category(
        self,
        auth_client,
        get_inventory_data_url,
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "categories" in res.data
        res_categories = res.data["categories"]
        assert type(res_categories) == dict

        assert "count" in res_categories
        assert type(res_categories["count"]) == int
        assert res_categories["count"] == 0

        assert "names" in res_categories
        assert isinstance(res_categories["names"], list)
        assert len(res_categories["names"]) == 0

    def test_inventory_data_suppliers_field(
        self,
        auth_client,
        get_inventory_data_url,
        user
    ):
        suppliers = SupplierFactory.create_batch(4, created_by=user)

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "suppliers" in res.data
        res_suppliers = res.data["suppliers"]
        assert type(res_suppliers) == dict

        assert "count" in res_suppliers
        assert type(res_suppliers["count"]) == int
        assert res_suppliers["count"] == len(suppliers)

        assert "names" in res_suppliers
        assert isinstance(res_suppliers["names"], list)
        assert all(
            supplier.name in res_suppliers["names"]
            for supplier in suppliers
        )

    def test_inventory_data_with_no_registered_supplier(
        self,
        auth_client,
        get_inventory_data_url,
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "suppliers" in res.data
        res_suppliers = res.data["suppliers"]
        assert type(res_suppliers) == dict

        assert "count" in res_suppliers
        assert type(res_suppliers["count"]) == int
        assert res_suppliers["count"] == 0

        assert "names" in res_suppliers
        assert isinstance(res_suppliers["names"], list)
        assert len(res_suppliers["names"]) == 0

    def test_inventory_data_variants_field(
        self,
        auth_client,
        get_inventory_data_url,
        user,
    ):
        variants = VariantFactory.create_batch(5, created_by=user)

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "variants" in res.data
        res_variants = res.data["variants"]
        assert isinstance(res_variants, list)
        assert len(res_variants) == len(variants)

        assert all(variant.name in res_variants for variant in variants)

    def test_inventory_data_with_no_registered_variant(
        self,
        auth_client,
        get_inventory_data_url,
    ):
        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        assert "variants" in res.data
        res_variants = res.data["variants"]
        assert isinstance(res_variants, list)
        assert len(res_variants) == 0

    def test_inventory_data_for_authenticated_user(
        self,
        auth_client,
        user,
        get_inventory_data_url
    ):
        # Create data for the authenticated user
        item = ItemFactory.create(created_by=user, in_inventory=True)
        supplier = SupplierFactory.create(created_by=user)
        category = CategoryFactory.create(created_by=user)
        variant = VariantFactory.create(created_by=user)

        # Create data for another user
        another_user = UserFactory.create()
        ItemFactory.create(created_by=another_user)
        SupplierFactory.create(created_by=another_user)
        CategoryFactory.create(created_by=another_user)
        VariantFactory.create(created_by=another_user)

        res = auth_client.get(get_inventory_data_url)

        assert res.status_code == 200

        # Verify that only the authenticated user's data is returned
        assert len(res.data["items"]) == 1
        assert res.data["items"][0] == {
            "name": item.name,
            "quantity": item.quantity
        }

        assert res.data["total_items"] == 1
        assert res.data["total_value"] == item.quantity * item.price
        assert res.data["total_quantity"] == item.quantity

        assert res.data["categories"]["count"] == 1
        assert category.name in res.data["categories"]["names"]

        assert res.data["suppliers"]["count"] == 1
        assert supplier.name in res.data["suppliers"]["names"]

        assert len(res.data["variants"]) == 1
        assert variant.name in res.data["variants"]
