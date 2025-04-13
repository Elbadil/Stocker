import pytest
from django.urls import reverse
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.client_orders.models import Client
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
        ClientFactory.create_batch(10, created_by=user)

        res = api_client.get(create_list_clients_url)
        assert res.status_code == 200

        assert isinstance(res.data, list)
        assert len(res.data) == 10

        # Verify that all clients belong to the authenticated user
        assert all(client["created_by"] == str(user.username)
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
            "age": 20
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
