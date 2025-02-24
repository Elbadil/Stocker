import pytest
import uuid
from apps.inventory.serializers import (
    CategorySerializer,
    VariantSerializer,
    VariantOptionSerializer,
    ItemSerializer
)
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import (
    ItemFactory,
    CategoryFactory,
    VariantFactory,
    VariantOptionFactory
)
from apps.inventory.models import Category, Variant, Item, VariantOption


@pytest.fixture
def random_uuid():
    return str(uuid.uuid4())

@pytest.fixture
def user(db):
    return UserFactory.create(username="adel")

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
def category_data(db, user):
    return {
        "created_by": user.id,
        "name": "Headphones"
    }

@pytest.fixture
def variant_option_data(db, item, variant):
    return {
        "item": item.id,
        "variant": variant.id,
        "body": "red"
    }


@pytest.mark.django_db
class TestCategorySerializer:
    """Tests for the CategorySerializer"""

    def test_category_creation_with_valid_data(self, category_data):
        serializer = CategorySerializer(data=category_data)
        assert serializer.is_valid()

        category = serializer.save()
        assert category.name == "Headphones"
        assert category.created_by is not None
        assert category.created_by.username == "adel"

    def test_category_creation_with_inexistent_created_by_id(
        self,
        random_uuid,
        category_data
    ):
        category_data['created_by'] = random_uuid
        serializer = CategorySerializer(data=category_data)

        assert not serializer.is_valid()
        assert "created_by" in serializer.errors
        assert (
            serializer.errors["created_by"] ==
            [f'Invalid pk "{random_uuid}" - object does not exist.']
        )
    
    def test_category_creation_fails_without_name(
        self,
        category_data
    ):
        category_data.pop('name')
        serializer = CategorySerializer(data=category_data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]
    
    def test_category_created_by_field_is_optional(
        self,
        category_data
    ):
        category_data.pop('created_by')
        serializer = CategorySerializer(data=category_data)

        assert serializer.is_valid()

        category = serializer.save()
        assert category.created_by is None
        assert category.name == "Headphones"

    def test_category_serializer_data_fields(self, category):
        serializer = CategorySerializer(category)
        
        assert "id" in serializer.data
        assert "created_by" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_category_serializer_data_fields_types(self, category):
        serializer = CategorySerializer(category)
        category_data = serializer.data

        assert type(category_data["id"]) == str
        assert type(category_data["created_by"]) == str
        assert type(category_data["name"]) == str
        assert type(category_data["created_at"]) == str
        assert type(category_data["updated_at"]) == str

    def test_category_serializer_data(self, user, category):
        serializer = CategorySerializer(category)
        category_data = serializer.data

        assert category_data["created_by"] == user.id
        assert category_data["name"] == "Headphones"


@pytest.mark.django_db
class TestVariantOptionSerializer:
    """Tests for the VariantOptionSerializer"""

    def test_variant_option_creation_with_valid_data(
        self,
        variant_option_data
    ):
        serializer = VariantOptionSerializer(data=variant_option_data)
        assert serializer.is_valid()

        variant_option = serializer.save()
        assert variant_option.body == "red"
        assert variant_option.item is not None
        assert variant_option.item.name == "Projector"
        assert variant_option.variant is not None
        assert variant_option.variant.name == "Color"

    def test_variant_option_creation_with_inexistent_item_id(
        self,
        random_uuid,
        variant_option_data
    ):
        variant_option_data["item"] = random_uuid
        serializer = VariantOptionSerializer(data=variant_option_data)

        assert not serializer.is_valid()
        assert "item" in serializer.errors
        assert (
            serializer.errors["item"] ==
            [f'Invalid pk "{random_uuid}" - object does not exist.']
        )

    def test_variant_option_creation_with_inexistent_variant_id(
        self,
        random_uuid,
        variant_option_data
    ):
        variant_option_data["variant"] = random_uuid
        serializer = VariantOptionSerializer(data=variant_option_data)

        assert not serializer.is_valid()
        assert "variant" in serializer.errors
        assert (
            serializer.errors["variant"] ==
            [f'Invalid pk "{random_uuid}" - object does not exist.']
        )

    def test_variant_option_creation_fails_without_body(
        self,
        variant_option_data
    ):
        variant_option_data.pop('body')
        serializer = VariantOptionSerializer(data=variant_option_data)

        assert not serializer.is_valid()
        assert "body" in serializer.errors
        assert serializer.errors["body"] == ["This field is required."]

    def test_variant_option_creation_item_field_is_optional(
        self,
        variant_option_data
    ):
        variant_option_data.pop('item')
        serializer = VariantOptionSerializer(data=variant_option_data)
        assert serializer.is_valid()

        variant_option = serializer.save()
        assert variant_option.item is None
        assert variant_option.body == "red"

    def test_variant_option_creation_variant_field_is_optional(
        self,
        variant_option_data
    ):
        variant_option_data.pop('variant')
        serializer = VariantOptionSerializer(data=variant_option_data)
        assert serializer.is_valid()

        variant_option = serializer.save()
        assert variant_option.variant is None
        assert variant_option.body == "red"

    def test_variant_option_serializer_data_fields(self, variant_option):
        serializer = VariantOptionSerializer(variant_option)

        assert "id" in serializer.data
        assert "item" in serializer.data
        assert "variant" in serializer.data
        assert "body" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_variant_option_serializer_data_fields_types(self, variant_option):
        serializer = VariantOptionSerializer(variant_option)
        variant_option_data = serializer.data

        assert type(variant_option_data["id"]) == str
        assert type(variant_option_data["item"]) == str
        assert type(variant_option_data["variant"]) == str
        assert type(variant_option_data["body"]) == str
        assert type(variant_option_data["created_at"]) == str
        assert type(variant_option_data["updated_at"]) == str

    def test_variant_option_serializer_data(
        self,
        item,
        variant,
        variant_option
    ):
        serializer = VariantOptionSerializer(variant_option)
        variant_option_data = serializer.data

        assert variant_option_data["item"] == item.id
        assert variant_option_data["variant"] == variant.id
        assert variant_option_data["body"] == "red"
