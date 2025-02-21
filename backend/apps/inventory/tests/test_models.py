import pytest
import os
import shutil
from django.conf import settings
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import (
    CategoryFactory,
    VariantFactory,
    ItemFactory,
    VariantOptionFactory
)
from apps.inventory.models import Category, Variant, Item, VariantOption


@pytest.fixture
def user(db):
	return UserFactory.create()

@pytest.fixture
def supplier(db):
    return SupplierFactory.create()

@pytest.fixture
def category(db):
    return CategoryFactory.create()

@pytest.fixture
def item(db):
    return ItemFactory.create()

@pytest.fixture
def item_data():
    return {
        "name": "Projector",
        "quantity": 4,
        "price": 199.99
    }

@pytest.fixture
def setup_cleanup_picture(item):
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )
    picture = SimpleUploadedFile('item_small.gif', small_gif, content_type='image/gif')

    yield picture

    user_item_images_folder = os.path.join(
        settings.MEDIA_ROOT,
        f"inventory/images/{item.created_by.id}"
    )
    if os.path.exists(user_item_images_folder):
        shutil.rmtree(user_item_images_folder)


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category Model"""

    def test_category_str_repr(self):
        user = UserFactory.create(username="adel")
        category = Category.objects.create(created_by=user, name="Headphones")
        assert category.__str__() == "Category: -Headphones- Added by -adel-"

    def test_category_with_no_created_by_str_repr(self):
        category = Category.objects.create(created_by=None, name="Headphones")
        assert category.__str__() == "Headphones"

    def test_category_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            Category.objects.create(name=None)

    def test_category_validation_fails_with_blank_name(self):
        category = Category(name="")
        with pytest.raises(ValidationError):
            category.full_clean()
    
    def test_category_creation_with_user(self):
        category = CategoryFactory.create()

        assert category.created_by is not None
        assert category.created_by.username is not None
        assert type(category.created_by.username) == str

    def test_category_creation_with_custom_user(self):
        user = UserFactory.create(username="adel")
        category = CategoryFactory.create(created_by=user)

        assert category.created_by is not None
        assert category.created_by.username is not None
        assert type(category.created_by.username) == str
        assert category.created_by.username == "adel"

    def test_category_with_multiple_items(self):
        category = CategoryFactory.create()
        ItemFactory.create(name="Projector", category=category)
        ItemFactory.create(name="Data Show", category=category)

        category_items = category.items.all()
        assert len(category_items) > 0

        category_item_names = [item.name for item in category_items]
        assert "Projector" in category_item_names
        assert "Data Show" in category_item_names
        assert len(category_item_names) == 2


@pytest.mark.django_db
class TestVariantModel:
    """Tests for the Variant Model"""

    def test_variant_str_repr(self):
        user = UserFactory.create(username="adel")
        variant = Variant.objects.create(created_by=user, name="Color")
        assert variant.__str__() == "Variant: -Color- Added by -adel-"

    def test_variant_with_no_created_by_str_repr(self):
        variant = Variant.objects.create(created_by=None, name="Color")
        assert variant.__str__() == "Color"

    def test_variant_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            Variant.objects.create(name=None)

    def test_variant_validation_fails_with_blank_name(self):
        variant = Variant(name="")
        with pytest.raises(ValidationError):
            variant.full_clean()

    def test_variant_creation_with_user(self):
        variant = VariantFactory.create()

        assert variant.created_by is not None
        assert variant.created_by.username is not None
        assert type(variant.created_by.username) == str

    def test_variant_creation_with_custom_user(self):
        user = UserFactory.create(username="adel")
        variant = VariantFactory.create(created_by=user)

        assert variant.created_by is not None
        assert variant.created_by.username is not None
        assert type(variant.created_by.username) == str
        assert variant.created_by.username == "adel"
    
    def test_variant_with_multiple_items(self):
        variant = VariantFactory.create()
        ItemFactory.create(name="Projector", variants=[variant])
        ItemFactory.create(name="Data Show", variants=[variant])

        variant_items = variant.items.all()
        assert len(variant_items) > 0

        variant_item_names = [item.name for item in variant_items]
        assert "Projector" in variant_item_names
        assert "Data Show" in variant_item_names
        assert len(variant_item_names) == 2


@pytest.mark.django_db
class TestItemModel:
    """Tests for the Item Model"""

    def test_item_str_repr(self):
        user = UserFactory.create(username="adel")
        item = ItemFactory.create(created_by=user, name="Projector")
        assert item.__str__() == "Projector by -adel-"

    def test_item_with_no_created_by_str_repr(self):
        item = ItemFactory.create(created_by=None, name="Projector")
        assert item.__str__() == "Projector"

    def test_item_validation_fails_with_blank_name(self):
        item = ItemFactory(name="")
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_item_creation_fails_without_name(self):
        with pytest.raises(IntegrityError):
            ItemFactory.create(name=None)

    def test_item_creation_fails_without_quantity(self, item_data):
        item_data.pop('quantity')
        with pytest.raises(IntegrityError):
            Item.objects.create(**item_data)
    
    def test_item_creation_fails_without_price(self, item_data):
        item_data.pop('price')
        with pytest.raises(IntegrityError):
            Item.objects.create(**item_data)

    def test_item_validation_fails_with_negative_quantity(self):
        item = ItemFactory.create(quantity=-1)
        with pytest.raises(ValidationError):
            item.full_clean()
    
    def test_item_validation_fails_with_negative_price(self):
        item = ItemFactory.create(price=-1)
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_item_creation_with_user(self):
        item = ItemFactory.create()

        assert item.created_by is not None
        assert item.created_by.username is not None
        assert type(item.created_by.username) == str

    def test_item_creation_with_custom_user(self):
        user = UserFactory.create(username="adel")
        item = ItemFactory.create(created_by=user)

        assert item.created_by is not None
        assert item.created_by.username is not None
        assert type(item.created_by.username) == str
        assert item.created_by.username == "adel"

    def test_item_creation_with_category(self):
        item = ItemFactory.create()

        assert item.category is not None
        assert isinstance(item.category, Category)
        assert item.category.name is not None
        assert type(item.category.name) == str

    def test_item_creation_with_custom_category(self):
        category = CategoryFactory.create(name="Headphones")
        item = ItemFactory.create(category=category)

        assert item.category is not None
        assert item.category.name is not None
        assert type(item.category.name) == str
        assert item.category.name == "Headphones"

    def test_item_creation_with_supplier(self):
        item = ItemFactory.create()

        assert item.supplier is not None
        assert item.supplier.name is not None
        assert type(item.supplier.name) == str

    def test_item_creation_with_custom_supplier(self):
        supplier = SupplierFactory.create(name="Ali Baba")
        item = ItemFactory.create(supplier=supplier)

        assert item.supplier is not None
        assert item.supplier.name is not None
        assert type(item.supplier.name) == str
        assert item.supplier.name == "Ali Baba"

    def test_item_creation_with_variants(self):
        item = ItemFactory.create()

        assert item.variants is not None
        assert len(item.variants.all()) == 3

    def test_item_creation_with_custom_variants(self):
        variant_1 = VariantFactory.create(name="Color")
        variant_2 = VariantFactory.create(name="Size")
        variant_3 = VariantFactory.create(name="Weight")
        item = ItemFactory.create(variants=[variant_1, variant_2, variant_3])

        assert item.variants is not None
        assert len(item.variants.all()) == 3

        variant_names = [variant.name for variant in item.variants.all()]
        assert "Color" in variant_names
        assert "Size" in variant_names
        assert "Weight" in variant_names

    def test_item_creation_with_picture(self, item, setup_cleanup_picture):
        item.picture = setup_cleanup_picture
        item.save()

        assert item.picture is not None
        assert "item_small.gif" in item.picture.name

    def test_item_creation_in_inventory_bool_field_default_value(
        self,
        item
    ):
        assert not item.in_inventory
        assert item.in_inventory == False

    def test_item_creation_updated_bool_field_default_value(self, item):
        assert not item.updated
        assert item.updated == False


@pytest.mark.django_db
class TestVarianOptionModel:
    """Tests for the VariantOption Model"""

    def test_variant_option_str_repr(self):
        user = UserFactory.create(username="adel")
        variant = VariantFactory.create(created_by=user, name="Color")
        item = ItemFactory.create(
            created_by=user,
            name="Projector",
            variants=[variant]
        )
        variant_option = VariantOptionFactory.create(
            item=item,
            variant=variant,
            body="red"
        )
        assert variant_option.__str__() == (
            f"Projector added by -adel- is available on Color: red"
        )

    def test_variant_option_creation_with_item(self):
        variant_option = VariantOptionFactory.create()

        assert variant_option.item is not None
        assert variant_option.item.name is not None
        assert type(variant_option.item.name) == str

    def test_variant_option_creation_with_custom_item(self):
        item = ItemFactory.create(name="Projector")
        variant_option = VariantOptionFactory.create(item=item)

        assert variant_option.item is not None
        assert variant_option.item.id == item.id
        assert variant_option.item.name is not None
        assert type(variant_option.item.name) == str
        assert variant_option.item.name == "Projector"

    def test_variant_option_creation_with_variant(self):
        variant_option = VariantOptionFactory.create()

        assert variant_option.variant is not None
        assert variant_option.variant.name is not None
        assert type(variant_option.variant.name) == str

    def test_variant_option_creation_with_custom_variant(self):
        variant = VariantFactory.create(name="Color")
        variant_option = VariantOptionFactory.create(variant=variant)

        assert variant_option.variant is not None
        assert variant_option.variant.id == variant.id
        assert variant_option.variant.name is not None
        assert type(variant_option.variant.name) == str
        assert variant_option.variant.name == "Color"

    def test_multiple_variant_option_creation_with_an_item(self):
        item = ItemFactory.create(name="Projector")
        VariantOptionFactory.create(item=item, body="red")
        VariantOptionFactory.create(item=item, body="blue")

        item_variant_options = VariantOption.objects.filter(item=item)
        assert len(item_variant_options) > 0

        item_variant_options_bodies = [
            variant_opt.body
            for variant_opt
            in item_variant_options
        ]

        assert "red" in item_variant_options_bodies
        assert "blue" in item_variant_options_bodies
        assert len(item_variant_options) == 2

    def test_multiple_variant_option_creation_with_a_variant(self):
        variant = VariantFactory.create(name="Color")
        VariantOptionFactory.create(variant=variant, body="red")
        VariantOptionFactory.create(variant=variant, body="blue")

        color_variant_options = VariantOption.objects.filter(variant=variant)
        assert len(color_variant_options) > 0

        color_variant_options_bodies = [
            variant_opt.body
            for variant_opt
            in color_variant_options
        ]

        assert "red" in color_variant_options_bodies
        assert "blue" in color_variant_options_bodies
        assert len(color_variant_options) == 2
