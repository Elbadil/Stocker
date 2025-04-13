import pytest
from django.urls import reverse
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


@pytest.fixture
def create_list_clients_url():
    return reverse("create_list_clients")

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
        # Authenticate the client as the given user
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
        # Authenticate the client as the given user
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
