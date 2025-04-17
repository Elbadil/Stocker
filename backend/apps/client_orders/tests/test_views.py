import pytest
import uuid
from typing import Union
from deepdiff import DeepDiff
from django.urls import reverse
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.inventory.factories import ItemFactory
from apps.client_orders.models import Client, ClientOrder, ClientOrderedItem
from apps.client_orders.factories import (
    CountryFactory,
    CityFactory,
    LocationFactory,
    AcquisitionSourceFactory,
    ClientFactory,
    OrderStatusFactory,
    ClientOrderFactory,
    ClientOrderedItemFactory,
)
from utils.serializers import date_repr_format, get_location


@pytest.fixture
def create_list_clients_url():
    return reverse("create_list_clients")

@pytest.fixture
def bulk_delete_clients_url():
    return reverse("bulk_delete_clients")

def client_url(client_id: str):
    """
    Returns the URL for the get_update_delete_clients view based on the provided
    client id.
    """
    return reverse("get_update_delete_clients", kwargs={"id": client_id})

@pytest.fixture
def client_data():
    return {
        "name": "Haitam",
    }

@pytest.fixture
def create_list_orders_url():
    return reverse("create_list_client_orders")

@pytest.fixture
def bulk_delete_orders_url():
    return reverse("bulk_delete_client_orders")

def order_url(order_id: str):
    return reverse("get_update_delete_client_orders",
                   kwargs={"id": order_id})

def ordered_item_url(order_id: str, item_id: Union[str, None]=None):
    """
    Returns the URL for the create_list_client_ordered_items or
    get_update_delete_client_ordered_items view based on the provided order ID
    and optionally item ID.
    """
    if item_id:
        return reverse("get_update_delete_client_ordered_items",
                       kwargs={"order_id": order_id, "id": item_id})
    return reverse("create_list_client_ordered_items",
                   kwargs={"order_id": order_id})

@pytest.mark.django_db
class TestCreateListClientsView:
    """Tests for the CreateListClients view."""

    def test_create_list_clients_requires_authentication(
        self,
        api_client,
        create_list_clients_url
    ):
        res = api_client.get(create_list_clients_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_clients_allowed_http_methods(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        get_res = auth_client.get(create_list_clients_url)
        assert get_res.status_code == 200

        put_res = auth_client.put(create_list_clients_url)
        assert put_res.status_code == 405

        post_res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert post_res.status_code == 201

        patch_res = auth_client.patch(create_list_clients_url)
        assert patch_res.status_code == 405

        delete_res = auth_client.delete(create_list_clients_url)
        assert delete_res.status_code == 405

    def test_create_client_fails_without_name(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        client_data.pop("name")
        res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("This field is required.")
    
    def test_create_client_fails_with_blank_name(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        client_data["name"] = ""
        res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("This field may not be blank.")

    def test_create_client_fails_with_existing_name(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        ClientFactory.create(name="Haitam")
        res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 400
        assert "name" in res.data
        assert res.data["name"][0].startswith("client with this name already exists.")
    
    def test_create_client_fails_with_invalid_email(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        client_data["email"] = "invalid_email"
        res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"][0].startswith("Enter a valid email address.")

    def test_create_client_with_valid_data(
        self,
        auth_client,
        client_data,
        create_list_clients_url
    ):
        res = auth_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 201
        assert res.data["name"] == client_data["name"]

        # Verify client is created and registered in the database with correct data
        client = Client.objects.filter(name=client_data["name"]).first()
        assert client is not None
        assert client.name == client_data["name"]

    def test_client_created_by_authenticated_user(
        self,
        user,
        api_client,
        client_data,
        create_list_clients_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create a client using the authenticated client
        res = api_client.post(
            create_list_clients_url,
            data=client_data,
            format='json'
        )
        assert res.status_code == 201

        # Verify the created client is associated with the authenticated user
        client = Client.objects.filter(name=client_data["name"]).first()
        assert client is not None
        assert str(client.created_by.id) == str(user.id)

    def test_list_clients_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_clients_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 10 clients for the authenticated user
        user_clients = ClientFactory.create_batch(10, created_by=user)

        # Create 5 clients for other users
        ClientFactory.create_batch(5)

        res = api_client.get(create_list_clients_url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == 10

        # Verify that all clients belong to the authenticated user
        assert all(client["created_by"] == str(user.username)
                   for client in res.data)
        assert all(client["id"] in [str(client.id) for client in user_clients]
                   for client in res.data)


@pytest.mark.django_db
class TestGetUpdateDeleteClientsView:
    """Tests for the GetUpdateDeleteClients view."""

    def test_get_update_delete_clients_requires_authentication(
        self,
        api_client,
        client,
    ):
        url = client_url(client.id)
        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_clients_allowed_http_methods(
        self,
        auth_client,
        client,
        client_data
    ):
        url = client_url(client.id)
        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        put_res = auth_client.put(url, data=client_data, format='json')
        assert put_res.status_code == 200

        post_res = auth_client.post(url)
        assert post_res.status_code == 405

        patch_res = auth_client.patch(url, data=client_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_client_operations_fail_with_inexistent_id(
        self,
        auth_client,
        random_uuid,
        client_data
    ):
        url = client_url(random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Client matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data=client_data, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No Client matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No Client matches the given query."

    def test_client_operations_fail_with_client_not_linked_to_authenticated_user(
        self,
        user,
        api_client,
        client_data
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create a client not linked to the authenticated user
        user_2 = UserFactory.create()
        client = ClientFactory.create(created_by=user_2, **client_data)

        # Verify the created client is not associated with the authenticated user
        assert str(client.created_by.id) != str(user.id)

        url = client_url(client.id)

        # Test GET request
        get_res = api_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No Client matches the given query."

        # Test PUT request
        put_res = api_client.put(url, data=client_data, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No Client matches the given query."

        # Test DELETE request
        delete_res = api_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No Client matches the given query."

    def test_get_client_with_valid_client(self, auth_client, user, client_data):
        client = ClientFactory.create(created_by=user, **client_data)
        url = client_url(client.id)

        res = auth_client.get(url)
        assert res.status_code == 200

    def test_client_response_data_fields(
        self,
        auth_client,
        client
    ):
        url = client_url(client.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        expected_fields = {
            "id",
            "created_by",
            "name",
            "age",
            "phone_number",
            "email",
            "sex",
            "location",
            "source",
            "total_orders",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(res.data.keys())

    def test_client_response_data_fields_types(
        self,
        auth_client,
        client
    ):
        url = client_url(client.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        assert isinstance(res.data["id"], str)
        assert isinstance(res.data["created_by"], str)
        assert isinstance(res.data["name"], str)
        assert isinstance(res.data["age"], int)
        assert isinstance(res.data["phone_number"], str)
        assert isinstance(res.data["email"], str)
        assert isinstance(res.data["sex"], str)
        assert isinstance(res.data["location"], dict)
        assert isinstance(res.data["source"], str)
        assert isinstance(res.data["total_orders"], int)
        assert isinstance(res.data["created_at"], str)
        assert isinstance(res.data["updated_at"], str)
        assert isinstance(res.data["updated"], bool)

    def test_client_response_data_fields_values(
        self,
        auth_client,
        client
    ):
        url = client_url(client.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        assert res.data["id"] == str(client.id)
        assert res.data["created_by"] == client.created_by.username
        assert res.data["name"] == client.name
        assert res.data["age"] == client.age
        assert res.data["phone_number"] == client.phone_number
        assert res.data["email"] == client.email
        assert res.data["sex"] == client.sex
        assert res.data["location"] == get_location(client.location)
        assert res.data["source"] == client.source.name
        assert res.data["total_orders"] == client.total_orders
        assert res.data["created_at"] == date_repr_format(client.created_at)
        assert res.data["updated_at"] == date_repr_format(client.updated_at)
        assert res.data["updated"] == client.updated

    def test_client_update(self, auth_client, client):
        client_data = {
            "name": "Safuan",
            "age": client.age + 2,
        }

        assert client.name != client_data["name"]
        assert client.age != client_data["age"]

        url = client_url(client.id)

        res = auth_client.put(url, data=client_data, format='json')
        assert res.status_code == 200

        assert res.data["name"] == client_data["name"]
        assert res.data["age"] == client_data["age"]

        # Verify that the client record has been updated
        client.refresh_from_db()
        assert client.name == client_data["name"]
        assert client.age == client_data["age"]

    def test_client_partial_update(self, auth_client, client):
        client_data = {
            "email": "safuan_new_email@example.com",
        }

        assert client.email != client_data["email"]

        url = client_url(client.id)

        res = auth_client.patch(url, data=client_data, format='json')
        assert res.status_code == 200

        assert res.data["email"] == client_data["email"]

        # Verify that the client record has been updated
        client.refresh_from_db()
        assert client.email == client_data["email"]

    def test_client_deletion_fails_with_linked_orders(
        self,
        auth_client,
        client,
        client_order
    ):
        url = client_url(client.id)

        assert client_order.client.id == client.id

        res = auth_client.delete(url)
        assert res.status_code == 400

        assert "error" in res.data
        assert res.data["error"] == (
            f"Client {client.name} is linked to existing orders. "
            "Manage orders before deletion."
        )

        # Verify that the client record has not been deleted
        client.refresh_from_db()
        assert Client.objects.filter(id=client.id).exists()

    def test_client_successful_deletion(self, auth_client, client):
        url = client_url(client.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the client record has been deleted
        assert not Client.objects.filter(id=client.id).exists()

    def test_client_deletion_registers_a_new_activity(self, auth_client, client):
        url = client_url(client.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that the client record has been deleted
        assert not Client.objects.filter(id=client.id).exists()

        # Verify that an activity record has been created for the client deletion
        assert (
            Activity.objects.filter(
                action="deleted",
                model_name="client",
                object_ref__contains=[client.name]
            ).exists()
        )

@pytest.mark.django_db
class TestBulkDeleteClientsView:
    """Test for the BulkDeleteClients view."""

    def test_bulk_delete_clients_requires_authentication(
        self,
        api_client,
        bulk_delete_clients_url
    ):
        res = api_client.delete(bulk_delete_clients_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_clients_allowed_http_methods(
        self,
        auth_client,
        client,
        bulk_delete_clients_url
    ):
        get_res = auth_client.get(bulk_delete_clients_url)
        assert get_res.status_code == 405

        post_res = auth_client.post(bulk_delete_clients_url)
        assert post_res.status_code == 405

        put_res = auth_client.put(bulk_delete_clients_url)
        assert put_res.status_code == 405

        patch_res = auth_client.patch(bulk_delete_clients_url)
        assert patch_res.status_code == 405
    
        delete_res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id]},
            format='json'
        )
        assert delete_res.status_code == 200

    def test_bulk_delete_clients_fails_without_list_of_ids(
        self,
        auth_client,
        bulk_delete_clients_url
    ):
        res = auth_client.delete(bulk_delete_clients_url)
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No IDs provided."

    def test_bulk_delete_clients_fails_with_invalid_uuids(
        self,
        auth_client,
        bulk_delete_clients_url
    ):
        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": ["invalid_uuid"]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid UUIDs."
        
        assert "invalid_ids" in res_error
        assert res_error["invalid_ids"] == ["invalid_uuid"]

    def test_bulk_delete_clients_fails_with_inexistent_ids(
        self,
        auth_client,
        bulk_delete_clients_url,
        client
    ):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id, random_id_1, random_id_2]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all clients could not be found."

        assert "missing_ids" in res_error
        missing_ids = res_error["missing_ids"]
        assert len(missing_ids) == 2
        assert random_id_1 in missing_ids
        assert random_id_2 in missing_ids

    def test_bulk_delete_clients_fails_with_unauthorized_clients(
        self,
        user,
        auth_client,
        bulk_delete_clients_url,
    ):
        user_clients = ClientFactory.create_batch(2, created_by=user)
        other_clients = ClientFactory.create_batch(3)

        clients_ids = [client.id for client in user_clients + other_clients]

        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": clients_ids},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all clients could not be found."

        assert "missing_ids" in res_error
        assert len(res_error["missing_ids"]) == len(other_clients)
        assert all(client.id in res_error["missing_ids"] for client in other_clients)

    def test_bulk_delete_clients_fails_with_all_clients_linked_to_orders(
        self,
        user,
        auth_client,
        bulk_delete_clients_url,
        client,
        client_order,
    ):
        # Create a second client and link it to another order
        client_2 = ClientFactory.create(created_by=user)
        client_order_2 = ClientOrderFactory.create(created_by=user, client=client_2)

        # Current clients list
        clients = [
            {
                "id": client.id,
                "name": client.name
            },
            {
                "id": client_2.id,
                "name": client_2.name
            }
        ]

        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id, client_2.id]},
            format='json'
        )
        assert res.status_code == 400
        res_data = res.json()
        assert "error" in res_data
        res_error = res_data["error"]

        assert "message" in res_error
        assert res_error["message"] == (
            "All selected clients are linked to existing orders. "
            "Manage orders before deletion."
        )
        assert "linked_clients" in res_error
        assert len(res_error["linked_clients"]) == 2
        
        assert clients[0] in res_error["linked_clients"]
        assert clients[1] in res_error["linked_clients"]

    def test_bulk_delete_clients_with_some_clients_linked_to_orders_and_others_not(
        self,
        user,
        auth_client,
        bulk_delete_clients_url,
        client,
    ):
        # Create a second client without linking it to an order
        client_2 = ClientFactory.create(created_by=user)

        # Create a third client and link it to an order
        client_3 = ClientFactory.create(created_by=user)
        client_order = ClientOrderFactory.create(created_by=user, client=client_3)

        client_with_order = {
            "id": client_3.id,
            "name": client_3.name
        }            

        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id, client_2.id, client_3.id]},
            format='json'
        )
        assert res.status_code == 207
        res_data = res.json()

        assert "message" in res_data
        assert res_data["message"] == (
            "2 clients deleted successfully, but 1 client could not be deleted "
            "because they are linked to existing orders."
        )

        assert "linked_clients" in res_data
        assert len(res_data["linked_clients"]) == 1
        assert client_with_order in res_data["linked_clients"]

        # Verify that the two clients without order were deleted
        assert not Client.objects.filter(id__in=[client.id, client_2.id]).exists()

        # Verify that the client with order was not deleted
        assert Client.objects.filter(id=client_3.id).exists()

    def test_bulk_delete_clients_succeeds_with_all_clients_not_linked_to_orders(
        self,
        user,
        auth_client,
        bulk_delete_clients_url,
        client,
    ):
        # Create a second client without linking it to an order
        client_2 = ClientFactory.create(created_by=user)
        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id, client_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 clients successfully deleted."

        # Verify that both clients were deleted
        assert not Client.objects.filter(id__in=[client.id, client_2.id]).exists()

    def test_bulk_delete_clients_registers_a_new_activity(
        self,
        user,
        auth_client,
        bulk_delete_clients_url,
        client,
    ):
        # Add another client
        client_2 = ClientFactory.create(created_by=user)

        res = auth_client.delete(
            bulk_delete_clients_url,
            data={"ids": [client.id, client_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 clients successfully deleted."

        # Verify that the two clients have been deleted
        assert not Client.objects.filter(id__in=[client.id, client_2.id]).exists()

        # Verify that a new activity has been created
        assert Activity.objects.filter(
            user=user,
            action="deleted",
            model_name="client",
            object_ref__contains=[client.name, client_2.name]
        ).exists()


@pytest.mark.django_db
class TestCreateListClientOrdersView:
    """Tests for CreateListClientOrdersView"""

    def test_create_list_order_view_requires_auth(
        self,
        api_client,
        create_list_orders_url
    ):
        res = api_client.get(create_list_orders_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_order_allowed_http_methods(
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

        patch_res = auth_client.patch(create_list_orders_url)
        assert patch_res.status_code == 405

        delete_res = auth_client.delete(create_list_orders_url)
        assert delete_res.status_code == 405

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
        assert "id" in res_data
        
        # Verify that the order was created
        assert ClientOrder.objects.filter(id=res_data["id"]).exists()

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
        order = ClientOrder.objects.filter(id=res_data["id"]).first()
        assert order is not None

        # Verify that the order was created by the authenticated user
        assert str(order.created_by.id) == str(user.id)
        assert "created_by" in res_data
        assert res_data["created_by"] == user.username

    def test_list_orders_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_orders_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 6 orders for the authenticated user
        user_orders = ClientOrderFactory.create_batch(6, created_by=user)

        # Create 5 orders for other users
        ClientOrderFactory.create_batch(5)

        res = api_client.get(create_list_orders_url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == 6

        # Verify that all orders belong to the authenticated user
        assert all(order["created_by"] == str(user.username)
                   for order in res.data)
    
        user_orders_ids = {str(order.id) for order in user_orders}
        assert all(
            order["id"] in user_orders_ids
            for order in res.data
        )


@pytest.mark.django_db
class TestGetUpdateDeleteClientOrdersView:
    """Tests for GetUpdateDeleteClientOrdersView"""

    def test_get_update_delete_order_view_requires_auth(
        self,
        api_client,
        client_order,
    ):
        url = order_url(client_order.id)

        res = api_client.get(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

        res = api_client.put(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

        res = api_client.patch(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

        res = api_client.delete(url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_update_delete_order_view_allowed_http_methods(
        self,
        auth_client,
        order_data,
        client_order
    ):
        url = order_url(client_order.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url)
        assert post_res.status_code == 405

        put_res = auth_client.put(url, data=order_data, format='json')
        assert put_res.status_code == 200

        patch_res = auth_client.patch(url, data=order_data, format='json')
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 204

    def test_order_operations_fail_with_inexistent_order_id(
        self,
        auth_client,
        order_data,
        random_uuid
    ):
        url = order_url(random_uuid)

        # Test GET request
        get_res = auth_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No ClientOrder matches the given query."

        # Test PUT request
        put_res = auth_client.put(url, data=order_data, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No ClientOrder matches the given query."

        # Test PATCH request
        patch_res = auth_client.patch(url, data=order_data, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No ClientOrder matches the given query."

        # Test DELETE request
        delete_res = auth_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in patch_res.data
        assert delete_res.data["detail"] == "No ClientOrder matches the given query."

    def test_order_operations_fail_with_order_not_linked_to_authenticated_user(
        self,
        user,
        api_client,
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create an order without linking it to the authenticated user
        client_order = ClientOrderFactory.create()
        url = order_url(client_order.id)

        # Verify that the order does not belong to the authenticated user
        assert str(client_order.created_by.id) != str(user.id)

        # Test GET request
        get_res = api_client.get(url)
        assert get_res.status_code == 404
        assert "detail" in get_res.data
        assert get_res.data["detail"] == "No ClientOrder matches the given query."

        # Test PUT request
        put_res = api_client.put(url, data={}, format='json')
        assert put_res.status_code == 404
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "No ClientOrder matches the given query."

        # Test PATCH request
        patch_res = api_client.patch(url, data={}, format='json')
        assert patch_res.status_code == 404
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "No ClientOrder matches the given query."

        # Test DELETE request
        delete_res = api_client.delete(url)
        assert delete_res.status_code == 404
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "No ClientOrder matches the given query."

    def test_get_order_with_valid_order_id(
        self,
        user,
        api_client,
        client_order
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        url = order_url(client_order.id)

        # Verify that the order belongs to the authenticated user
        assert str(client_order.created_by.id) == str(user.id)

        res = api_client.get(url)
        assert res.status_code == 200

    def test_order_response_data_fields(self, auth_client, client_order):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()
        
        expected_fields = {
            "id",
            "reference_id",
            "created_by",
            "client",
            "ordered_items",
            "delivery_status",
            "payment_status",
            "tracking_number",
            "shipping_address",
            "shipping_cost",
            "source",
            "net_profit",
            "linked_sale",
            "created_at",
            "updated_at",
            "updated"
        }

        assert expected_fields.issubset(res_data.keys())

    def test_order_response_data_fields_types(
        self,
        auth_client,
        client_order,
        ordered_item,
        sale
    ):
        # Link sale to order
        client_order.sale = sale
        client_order.save()

        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert isinstance(res_data['id'], str)
        assert isinstance(res_data['reference_id'], str)
        assert isinstance(res_data['created_by'], str)
        assert isinstance(res_data['client'], str)
        assert isinstance(res_data['ordered_items'], list)
        assert isinstance(res_data['delivery_status'], str)
        assert isinstance(res_data['payment_status'], str)
        assert isinstance(res_data['tracking_number'], str)
        assert isinstance(res_data['shipping_address'], dict)
        assert isinstance(res_data['shipping_cost'], float)
        assert isinstance(res_data['source'], str)
        assert isinstance(res_data['net_profit'], float)
        assert isinstance(res_data['linked_sale'], str)
        assert isinstance(res_data['created_at'], str)
        assert isinstance(res_data['updated_at'], str)
        assert isinstance(res_data["updated"], bool)

    def test_order_response_data_for_general_fields(self, auth_client, client_order):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data["id"] == str(client_order.id)
        assert res_data["reference_id"] == client_order.reference_id
        assert res_data["created_by"] == client_order.created_by.username
        assert res_data["created_at"] == date_repr_format(client_order.created_at)
        assert res_data["updated_at"] == date_repr_format(client_order.updated_at)
        assert res_data["updated"] == client_order.updated

    def test_order_response_data_for_client_and_source_fields(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data["client"] == client_order.client.name
        assert res_data["source"] == client_order.source.name

    def test_order_response_data_for_ordered_items_field(
        self,
        auth_client,
        client_order,
        ordered_item
    ):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert len(res_data["ordered_items"]) == 1

        assert (
            res_data["ordered_items"][0]["item"] ==
            ordered_item.item.name
        )
        assert (
            res_data["ordered_items"][0]["ordered_quantity"] ==
            ordered_item.ordered_quantity
        )
        assert (
            res_data["ordered_items"][0]["ordered_price"] ==
            float(ordered_item.ordered_price)
        )

    def test_order_response_data_for_shipping_address_field(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert (
            res_data["shipping_address"]["street_address"]
            == client_order.shipping_address.street_address
        )
        assert (
            res_data["shipping_address"]["city"]
            == client_order.shipping_address.city.name
        )
        assert (
            res_data["shipping_address"]["country"]
            == client_order.shipping_address.country.name
        )

    def test_order_response_data_for_status_and_tracking_number_field(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data["delivery_status"] == client_order.delivery_status.name
        assert res_data["payment_status"] == client_order.payment_status.name
        assert res_data["tracking_number"] == client_order.tracking_number

    def test_order_response_data_for_financial_fields(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()

        assert res_data["shipping_cost"] == float(client_order.shipping_cost)
        assert res_data["net_profit"] == float(client_order.net_profit)
     
    def test_order_response_data_for_linked_sale_field(
        self,
        auth_client,
        client_order,
        sale
    ):
        # Link sale to order
        client_order.sale = sale
        client_order.save()

        url = order_url(client_order.id)

        res = auth_client.get(url)
        assert res.status_code == 200

        res_data = res.json()
        assert res_data["linked_sale"] == str(sale.id)

    def test_order_update(
        self,
        auth_client,
        delivered_status,
        order_data,
        client_order
    ):
        order_data["delivery_status"] = delivered_status.name
        order_data["tracking_number"] = "123456789"

        # Verify that order's delivery status and tracking number are different
        # than the ones in the request
        client_order.delivery_status.name != order_data["delivery_status"] 
        client_order.tracking_number != order_data["tracking_number"]

        res = auth_client.put(order_url(client_order.id), order_data, format="json")

        assert res.status_code == 200
        res_data = res.json()

        assert "delivery_status" in res_data

        # Verify that order delivery status has been set to delivered
        assert res_data["delivery_status"] == order_data["delivery_status"] 
        assert res_data["tracking_number"] == order_data["tracking_number"]

        # Verify that order record has been updated
        assert res_data["updated"]
        client_order.refresh_from_db()
        assert client_order.updated
        assert client_order.delivery_status.name == order_data["delivery_status"] 
        assert client_order.tracking_number == order_data["tracking_number"]

    def test_order_partial_update(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.patch(url, {"tracking_number": "123456789"}, format="json")

        assert res.status_code == 200
        res_data = res.json()

        assert "tracking_number" in res_data
        assert res_data["tracking_number"] == "123456789"

        # Verify that order record has been updated
        assert res_data["updated"]
        client_order.refresh_from_db()
        assert client_order.updated
        assert client_order.tracking_number == "123456789"

    def test_order_deletion(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that order record has been deleted
        assert not ClientOrder.objects.filter(id=client_order.id).exists()

    def test_order_deletion_deletes_linked_ordered_items(
        self,
        auth_client,
        ordered_item,
        client_order
    ):
        url = order_url(client_order.id)

        assert ordered_item.order.id == client_order.id
        assert len(client_order.ordered_items.all()) > 0

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that order record has been deleted
        assert not ClientOrder.objects.filter(id=client_order.id).exists()

        # Verify that linked ordered item record has been deleted
        assert not ClientOrderedItem.objects.filter(
            order__id=client_order.id
        ).exists()

    def test_order_deletion_resets_inventory_quantities_if_not_linked_to_a_sale(
        self,
        auth_client,
        ordered_item,
        client_order
    ):
        item_in_inventory = ordered_item.item
        item_quantity = item_in_inventory.quantity
        ordered_quantity = ordered_item.ordered_quantity

        # Verify that order is not linked to sale
        assert client_order.sale is None

        url = order_url(client_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that order record has been deleted
        assert not ClientOrder.objects.filter(id=client_order.id).exists()

        # Verify that linked ordered item record has been deleted
        assert not ClientOrderedItem.objects.filter(
            order__id=client_order.id
        ).exists()

        # Verify that item's quantity has been reset
        item_in_inventory.refresh_from_db()
        assert item_in_inventory.quantity != item_quantity
        assert item_in_inventory.quantity == item_quantity + ordered_quantity

    def test_order_deletion_registers_a_new_activity(
        self,
        auth_client,
        client_order
    ):
        url = order_url(client_order.id)

        res = auth_client.delete(url)
        assert res.status_code == 204

        # Verify that an activity record has been created for the order deletion
        assert (
            Activity.objects.filter(
                action="deleted",
                model_name="client order",
                object_ref__contains=[client_order.reference_id]
            ).exists()
        )


@pytest.mark.django_db
class TestBulkDeleteClientOrdersView:
    """Tests for BulkDeleteClientOrders view"""

    def test_bulk_delete_orders_view_requires_auth(
        self,
        api_client,
        bulk_delete_orders_url
    ):
        res = api_client.delete(bulk_delete_orders_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_bulk_delete_orders_view_allowed_http_methods(
        self,
        auth_client,
        client_order,
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

        put_res = auth_client.put(bulk_delete_orders_url)
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(bulk_delete_orders_url)
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [client_order.id]},
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

    def test_bulk_delete_orders_fails_with_invalid_uuids(
        self,
        auth_client,
        bulk_delete_orders_url
    ):
        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": ["invalid_uuid_1", "invalid_uuid_2"]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all provided IDs are not valid UUIDs."

        assert "invalid_ids" in res_error
        assert "invalid_uuid_1" in res_error["invalid_ids"]
        assert "invalid_uuid_2" in res_error["invalid_ids"]

    def test_bulk_delete_orders_fails_with_nonexistent_uuids(
        self,
        auth_client,
        bulk_delete_orders_url
    ):
        random_uuid_1 = str(uuid.uuid4())
        random_uuid_2 = str(uuid.uuid4())
        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [random_uuid_1, random_uuid_2]},
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        res_error = res.data["error"]

        assert "message" in res_error
        assert res_error["message"] == "Some or all selected orders could not be found."

        assert "missing_ids" in res_error
        assert random_uuid_1 in res_error["missing_ids"]
        assert random_uuid_2 in res_error["missing_ids"]

    def test_bulk_delete_orders_fails_with_unauthorized_orders(
        self,
        user,
        auth_client,
        bulk_delete_orders_url
    ):
        user_orders = ClientOrderFactory.create_batch(2, created_by=user)
        other_orders = ClientOrderFactory.create_batch(3)

        orders_ids = [order.id for order in user_orders + other_orders]

        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": orders_ids},
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

    def test_bulk_delete_orders_with_valid_orders(
        self,
        user,
        auth_client,
        client_order,
        bulk_delete_orders_url
    ):
        # Create another order
        client_order_2 = ClientOrderFactory.create(created_by=user)

        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [client_order.id, client_order_2.id]},
            format='json'
        )
        assert res.status_code == 200

        # Verify that the two orders have been deleted
        assert not ClientOrder.objects.filter(
            id__in=[client_order.id, client_order_2.id]
        ).exists()

    def test_bulk_delete_orders_deletes_linked_ordered_items(
        self,
        user,
        auth_client,
        client_order,
        ordered_item,
        bulk_delete_orders_url
    ):
        # Verify that the ordered item is linked to the order
        assert str(ordered_item.order.id) == str(client_order.id)

        # Create another order with another ordered_item
        item_2 = ItemFactory.create(created_by=user, in_inventory=True)
        client_order_2 = ClientOrderFactory.create(created_by=user)
        ordered_item_2 = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order_2,
            item=item_2,
            ordered_quantity=item_2.quantity - 1
        )

        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [client_order.id, client_order_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 client orders successfully deleted."

        # Verify that the two orders have been deleted
        assert not ClientOrder.objects.filter(
            id__in=[client_order.id, client_order_2.id]
        ).exists()

        # Verify that linked ordered items have been deleted
        assert not ClientOrderedItem.objects.filter(
            order__id__in=[client_order.id, client_order_2.id]
        ).exists()

    def test_bulk_delete_orders_resets_inventory_quantities_if_not_linked_to_sales(
        self,
        user,
        auth_client,
        client_order,
        ordered_item,
        bulk_delete_orders_url
    ):
        # Verify that the ordered item is linked to the order
        assert str(ordered_item.order.id) == str(client_order.id)

        item_1 = ordered_item.item
        item_1_quantity = item_1.quantity
 
        # Create another order with another ordered_item
        item_2 = ItemFactory.create(created_by=user, in_inventory=True)
        item_2_quantity = item_2.quantity
        client_order_2 = ClientOrderFactory.create(created_by=user)
        ordered_item_2 = ClientOrderedItemFactory.create(
            created_by=user,
            order=client_order_2,
            item=item_2,
            ordered_quantity=item_2_quantity - 1
        )

        # Verify that the orders are not linked to a sale
        assert client_order.sale is None
        assert client_order_2.sale is None

        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [client_order.id, client_order_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 client orders successfully deleted."

        # Verify that the two order have been deleted
        assert not ClientOrder.objects.filter(
            id__in=[client_order.id, client_order_2.id]
        ).exists()

        # Verify that the linked ordered items have been deleted
        assert not ClientOrderedItem.objects.filter(
            order__id__in=[client_order.id, client_order_2.id]
        ).exists()

        # Verify that the ordered items's inventory quantity has been reset
        item_1.refresh_from_db()
        assert item_1.quantity != item_1_quantity
        assert item_1.quantity == item_1_quantity + ordered_item.ordered_quantity

        item_2.refresh_from_db()
        assert item_2.quantity != item_2_quantity
        assert item_2.quantity == item_2_quantity + ordered_item_2.ordered_quantity

    def test_bulk_delete_orders_registers_a_new_activity(
        self,
        user,
        auth_client,
        client_order,
        bulk_delete_orders_url
    ):
        # Create another order
        client_order_2 = ClientOrderFactory.create(created_by=user)

        res = auth_client.delete(
            bulk_delete_orders_url,
            data={"ids": [client_order.id, client_order_2.id]},
            format='json'
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert res.data["message"] == "2 client orders successfully deleted."

        # Verify that the two orders have been deleted
        assert not ClientOrder.objects.filter(
            id__in=[client_order.id, client_order_2.id]
        ).exists()

        # Verify that a new activity has been created
        assert Activity.objects.filter(
            user=user,
            action="deleted",
            model_name="client order",
            object_ref__contains=[
                client_order.reference_id,
                client_order_2.reference_id
            ]
        ).exists()


@pytest.mark.django_db
class TestCreateListClientOrderedItemsView:
    """Test class for the CreateListClientOrderedItems view"""

    def test_create_list_ordered_items_view_requires_auth(
        self,
        api_client,
        client_order,
        ordered_item_data
    ):
        url = ordered_item_url(client_order.id)

        res = api_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_ordered_items_view_allowed_http_methods(
        self,
        auth_client,
        client_order,
        ordered_item_data
    ):
        url = ordered_item_url(client_order.id)

        get_res = auth_client.get(url)
        assert get_res.status_code == 200

        post_res = auth_client.post(url, data=ordered_item_data, format='json')
        assert post_res.status_code == 201

        put_res = auth_client.put(url, data=ordered_item_data, format='json')
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(url, data=ordered_item_data, format='json')
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
        random_uuid,
    ):
        url = ordered_item_url(random_uuid)

        res = auth_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{random_uuid}' does not exist."

    def test_create_list_ordered_items_fails_with_unauthorized_order(
        self,
        api_client,
        user,
        ordered_item_data,
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create an order with a different user
        order = ClientOrderFactory.create()

        # Verify the created order is not linked to the authenticated user
        assert str(order.created_by.id) != str(user.id)

        url = ordered_item_url(order.id)

        res = api_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 404
        assert "detail" in res.data
        assert res.data["detail"] == f"Order with id '{order.id}' does not exist."

    def test_create_ordered_item_with_valid_order_id_and_data(
        self,
        auth_client,
        ordered_item_data,
        client_order
    ):
        url = ordered_item_url(client_order.id)

        res = auth_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 201

        # Verify that the ordered item has been created
        assert "id" in res.data
        ordered_item = ClientOrderedItem.objects.filter(id=res.data["id"]).first()
        assert ordered_item is not None

        # Verify that the created ordered item is linked to the correct order
        assert "order" in res.data
        assert str(res.data["order"]) == str(client_order.id)
        assert str(ordered_item.order.id) == (client_order.id)

    def test_ordered_item_created_by_authenticated_user(
        self,
        api_client,
        user,
        ordered_item_data,
        client_order
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        url = ordered_item_url(client_order.id)

        res = api_client.post(url, data=ordered_item_data, format='json')
        assert res.status_code == 201

        # Verify that the ordered item has been created
        assert "id" in res.data
        ordered_item = ClientOrderedItem.objects.filter(id=res.data["id"]).first()
        assert ordered_item is not None

        # Verify that the created ordered item is linked to the correct user
        assert "created_by" in res.data
        assert res.data["created_by"] == user.username
        assert str(ordered_item.created_by.id) == str(user.id)

    def test_list_ordered_items_to_authenticated_user(
        self,
        api_client,
        user,
        client_order
    ):
        # Authenticate the api client with the given user
        api_client.force_authenticate(user=user)

        # Create 5 ordered items for the order and authenticated user
        user_items = ClientOrderedItemFactory.create_batch(
            5, order=client_order, created_by=user
        )

        # Create 4 ordered items for other orders and users
        ClientOrderedItemFactory.create_batch(4)

        url = ordered_item_url(client_order.id)

        res = api_client.get(url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == len(user_items)

        # Verify that all ordered items belong to the correct order and user
        assert all(
            str(item["order"]) == str(client_order.id)
            and item["created_by"] == user.username
            for item in res.data
        )

        user_item_ids = {str(item.id) for item in user_items}
        assert all(
            str(item["id"]) in user_item_ids
            for item in res.data
        )
