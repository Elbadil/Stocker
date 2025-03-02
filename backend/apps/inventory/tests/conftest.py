import pytest
import uuid
import os
import shutil
from rest_framework.test import APIClient
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import (
    CategoryFactory,
    VariantFactory,
    VariantOptionFactory,
    ItemFactory
)


@pytest.fixture
def user(db):
    return UserFactory.create(username="adel")

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def access_token(api_client, user):
    login_url = reverse('login')
    res = api_client.post(
        login_url,
        data={
            'email': user.email,
            'password': "pw"
        },
        format='json'
    )
    return res.data["access_token"]

@pytest.fixture
def auth_client(api_client, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client

@pytest.fixture
def random_uuid():
    return str(uuid.uuid4())

@pytest.fixture
def supplier(db, user):
    return SupplierFactory.create(created_by=user, name="Casa")

@pytest.fixture
def category(db, user):
    return CategoryFactory.create(created_by=user, name="Headphones")

@pytest.fixture
def item(db, user):
    return ItemFactory.create(created_by=user, name="Projector")

@pytest.fixture
def variant(db, user):
    return VariantFactory.create(created_by=user, name="Color")

@pytest.fixture
def variant_option(db, item, variant):
    return VariantOptionFactory.create(
        item=item,
        variant=variant,
        body="red"
    )

@pytest.fixture
def category_data(user):
    return {
        "created_by": user.id,
        "name": "Headphones"
    }

@pytest.fixture
def variant_option_data(item, variant):
    return {
        "item": item.id,
        "variant": variant.id,
        "body": "red"
    }

@pytest.fixture
def variant_data(user):
    return {
        "created_by": user.id,
        "name": "Color"
    }

@pytest.fixture
def item_data():
    return {
        "name": "Projector",
        "quantity": 2,
        "price": 199.99,
    }

@pytest.fixture
def small_gif():
    return (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )

@pytest.fixture
def setup_cleanup_picture(user, small_gif):
    picture = SimpleUploadedFile('item_small.gif', small_gif, content_type='image/gif')

    yield picture

    user_item_images_folder = os.path.join(
        settings.MEDIA_ROOT,
        f"inventory/images/{user.id}"
    )
    if os.path.exists(user_item_images_folder):
            shutil.rmtree(user_item_images_folder)