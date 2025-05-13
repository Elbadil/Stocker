import pytest
from django.urls import reverse
from apps.sales.models import Sale, SoldItem
from apps.sales.factories import SaleFactory, SoldItemFactory


@pytest.fixture
def create_list_sales_url():
    return reverse('create_list_sales')


@pytest.mark.django_db
class TestCreateListSalesView:
    """Tests for the create list sales view"""

    def test_create_list_sales_view_requires_auth(self, api_client, create_list_sales_url):
        res = api_client.get(create_list_sales_url)
        assert res.status_code == 403
        assert "detail" in res.data
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_create_list_sales_allowed_http_methods(
        self,
        auth_client,
        sale_data,
        create_list_sales_url
    ):
        get_res = auth_client.get(create_list_sales_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(create_list_sales_url, data=sale_data, format='json')
        assert post_res.status_code == 201

        put_res = auth_client.put(create_list_sales_url, data=sale_data, format='json')
        assert put_res.status_code == 405
        assert "detail" in put_res.data
        assert put_res.data["detail"] == "Method \"PUT\" not allowed."

        patch_res = auth_client.patch(create_list_sales_url, data=sale_data, format='json')
        assert patch_res.status_code == 405
        assert "detail" in patch_res.data
        assert patch_res.data["detail"] == "Method \"PATCH\" not allowed."

        delete_res = auth_client.delete(create_list_sales_url)
        assert delete_res.status_code == 405
        assert "detail" in delete_res.data
        assert delete_res.data["detail"] == "Method \"DELETE\" not allowed."

    def test_sale_creation_succeeds(self, auth_client, sale_data, create_list_sales_url):
        res = auth_client.post(create_list_sales_url, data=sale_data, format='json')
        assert res.status_code == 201

        res_data = res.json()
        assert "id" in res_data

        # Verify that Sale was created
        sale = Sale.objects.filter(id=res_data["id"]).first()
        assert isinstance(sale, Sale)

    def test_sale_created_by_authenticated_user(
        self,
        user,
        api_client,
        sale_data,
        create_list_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        res = api_client.post(
            create_list_sales_url,
            data=sale_data,
            format='json'
        )
        assert res.status_code == 201

        res_data = res.json()
        assert "created_by" in res_data
        assert res_data["created_by"] == user.username
        assert "id" in res_data

        # Verify that Sale was created with the authenticated user
        sale = Sale.objects.filter(id=res_data["id"]).first()
        assert isinstance(sale, Sale)
        assert str(sale.created_by.id) == str(user.id)

    def test_list_sales_to_authenticated_user(
        self,
        user,
        api_client,
        create_list_sales_url
    ):
        # Authenticate the api client as the given user
        api_client.force_authenticate(user=user)

        # Create 6 sales for the authenticated user
        user_sales = SaleFactory.create_batch(6, created_by=user)

        # Create 5 sales for other users
        SaleFactory.create_batch(5)

        res = api_client.get(create_list_sales_url)
        assert res.status_code == 200

        res_data = res.json()
        assert len(res_data) == 6

        # Verify that all sales belong to the authenticated user
        assert all(sale["created_by"] == str(user.username)
                   for sale in res_data)

        user_sales_ids = {str(sale.id) for sale in user_sales}
        assert all(
            sale["id"] in user_sales_ids
            for sale in res_data
        )

