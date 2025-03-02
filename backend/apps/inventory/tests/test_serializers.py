import pytest
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.inventory.serializers import (
    CategorySerializer,
    VariantSerializer,
    VariantOptionSerializer,
    ItemSerializer
)
from apps.base.models import Activity
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import ItemFactory
from apps.inventory.models import Category
import json


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
    
    def test_category_update(self, category, category_data):
        category_name = category.name
        category_data["name"] = "Headsets"

        serializer = CategorySerializer(category, data=category_data)
        assert serializer.is_valid()

        category_update = serializer.save()
        assert category_update.name == "Headsets"
        assert category_name != category_update.name
    
    def test_category_partial_update(self, category):
        category_name = category.name

        serializer = CategorySerializer(
            category,
            data={"name": "Headsets"},
            partial=True
        )
        assert serializer.is_valid()

        category_update = serializer.save()
        assert category_update.name == "Headsets"
        assert category_name != category_update.name


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
    
    def test_variant_option_update(self, variant_option, variant_option_data):
        variant_option_body = variant_option.body
        variant_option_data["body"] = "green"

        serializer = VariantOptionSerializer(
            variant_option,
            data=variant_option_data
        )
        assert serializer.is_valid()

        varian_option_update = serializer.save()
        assert varian_option_update.body == "green"
        assert variant_option_body != varian_option_update.body

    def test_variant_option_partial_update(self, variant_option):
        variant_option_body = variant_option.body

        serializer = VariantOptionSerializer(
            variant_option,
            data={"body": "green"},
            partial=True
        )
        assert serializer.is_valid()

        variant_option_update = serializer.save()
        assert variant_option_update.body == "green"
        assert variant_option_body != variant_option_update.body


@pytest.mark.django_db
class TestVariantSerializer:
    """Tests for the VariantSerializer"""

    def test_variant_creation_with_valid_data(self, variant_data):
        serializer = VariantSerializer(data=variant_data)
        assert serializer.is_valid()

        variant = serializer.save()
        assert variant.name == "Color"
        assert variant.created_by is not None
        assert variant.created_by.username == "adel"

    def test_variant_creation_with_inexistent_created_by_id(
        self,
        random_uuid,
        variant_data
    ):
        variant_data["created_by"] = random_uuid
        serializer = VariantSerializer(data=variant_data)

        assert not serializer.is_valid()
        assert "created_by" in serializer.errors
        assert (
            serializer.errors["created_by"] ==
            [f'Invalid pk "{random_uuid}" - object does not exist.']
        )

    def test_variant_creation_without_name(self, variant_data):
        variant_data.pop('name')
        serializer = VariantSerializer(data=variant_data)

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]

    def test_variant_creation_created_by_field_is_optional(
        self,
        variant_data
    ):
        variant_data.pop('created_by')
        serializer = VariantSerializer(data=variant_data)
        assert serializer.is_valid()

        variant = serializer.save()
        assert variant.created_by is None
        assert variant.name == "Color"
    
    def test_variant_serializer_data_fields(self, variant):
        serializer = VariantSerializer(variant)

        assert "id" in serializer.data
        assert "created_by" in serializer.data
        assert "name" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data

    def test_variant_serializer_data_fields_types(self, variant):
        serializer = VariantSerializer(variant)
        variant_data = serializer.data

        assert type(variant_data["id"]) == str
        assert type(variant_data["created_by"]) == str
        assert type(variant_data["name"]) == str
        assert type(variant_data["created_at"]) == str
        assert type(variant_data["updated_at"]) == str

    def test_variant_serializer_data(
        self,
        user,
        variant,
    ):
        serializer = VariantSerializer(variant)
        variant_data = serializer.data

        assert variant_data["created_by"] == user.id
        assert variant_data["name"] == "Color"

    def test_variant_update(self, variant, variant_data):
        variant_name = variant.name
        variant_data["name"] = "Size"

        serializer = VariantSerializer(variant, data=variant_data)
        assert serializer.is_valid()

        varian_update = serializer.save()
        assert varian_update.name == "Size"
        assert variant_name != varian_update.name

    def test_variant_partial_update(self, variant):
        variant_name = variant.name

        serializer = VariantSerializer(
            variant,
            data={"name": "Size"},
            partial=True
        )
        assert serializer.is_valid()

        variant_update = serializer.save()
        assert variant_update.name == "Size"
        assert variant_name != variant_update.name


@pytest.mark.django_db
class TestItemSerializer:
    """Tests for the ItemSerializer"""

    def test_item_creation_with_valid_data(self, user, item_data):
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.name == "Projector"
        assert item.quantity == 2
        assert item.price == Decimal('199.99')

        assert item.created_by is not None
        assert item.created_by.username == "adel"
    
    def test_item_creation_fails_without_name(self, user, item_data):
        item_data.pop('name')
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["This field is required."]
    
    def test_item_creation_fails_with_existing_name(self, user, item_data):
        item = ItemFactory.create(
            created_by=user,
            name="Projector",
            quantity=2,
            price=199.99
        )
        assert item.name == item_data["name"]

        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert serializer.errors["name"] == ["Item with this name already exists."]

    def test_item_creation_fails_without_quantity(self, user, item_data):
        item_data.pop('quantity')
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "quantity" in serializer.errors
        assert serializer.errors["quantity"] == ["This field is required."]
    
    def test_item_creation_fails_with_negative_quantity(self, user, item_data):
        item_data["quantity"] = -2
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "quantity" in serializer.errors
        assert(
            serializer.errors["quantity"] == 
            ["Ensure this value is greater than or equal to 0."]
        )

    def test_item_creation_fails_without_price(self, user, item_data):
        item_data.pop('price')
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "price" in serializer.errors
        assert serializer.errors["price"] == ["This field is required."]

    def test_item_creation_fails_with_negative_price(self, user, item_data):
        item_data["price"] = -22
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "price" in serializer.errors
        assert(
            serializer.errors["price"] == 
            ["Ensure this value is greater than or equal to 0.0."]
        )

    def test_item_creation_category_field_is_optional(self, user, item_data):
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert "category" not in item_data
        assert serializer.is_valid()

        item = serializer.save()
        assert item.category is None
    
    def test_item_serializer_creates_or_retrieves_category_by_name(
        self,
        user,
        item_data
    ):
        item_data["category"] = "Headsets"
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.category is not None
        assert item.category.name == "Headsets"

    def test_item_creation_with_existing_category(
        self,
        user,
        category,
        item_data
    ):
        assert isinstance(category, Category)

        item_data["category"] = category.name
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.category is not None
        assert item.category.name == "Headphones"
        assert str(category.id) == str(item.category.id)

    def test_item_serializer_creates_new_category_if_not_exist(
        self,
        user,
        item_data
    ):
        # Headsets Category before item creation
        headsets_category = Category.objects.filter(name="Headsets").first()
        assert not headsets_category

        item_data["category"] = "Headsets"
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.category is not None
        assert item.category.name == "Headsets"

        # Headsets Category after item creation
        headsets_category = Category.objects.filter(name="Headsets").first()
        assert headsets_category is not None
        assert str(headsets_category.id) == str(item.category.id)

    def test_item_creation_supplier_field_is_optional(self, user, item_data):
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert "supplier" not in item_data
        assert serializer.is_valid()

        item = serializer.save()
        assert item.supplier is None
    
    def test_item_serializer_retrieves_supplier_by_name(
        self,
        user,
        item_data
    ):
        supplier = SupplierFactory.create(created_by=user, name="Ali")
        item_data["supplier"] = "Ali"
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.supplier is not None
        assert item.supplier.name == "Ali"
        assert str(supplier.id) == str(item.supplier.id)

    def test_item_creation_with_valid_supplier(self, user, supplier, item_data):
        item_data["supplier"] = supplier.name
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.supplier is not None
        assert item.supplier.name == "Casa"
    
    def test_item_creation_fails_with_inexistent_supplier(
        self,
        user,
        item_data
    ):
        random_supplier_name = "Random"
        item_data["supplier"] = random_supplier_name
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "supplier" in serializer.errors
        assert serializer.errors["supplier"] == ([
            f"Supplier '{random_supplier_name}' does not exist. "
             "Please create a new supplier if this is a new entry."
        ])

    def test_item_serializer_rejects_supplier_not_owned_by_user(
        self,
        user,
        item_data
    ):
        user_2 = UserFactory.create()
        supplier = SupplierFactory.create(created_by=user_2, name="Ali")
        assert str(supplier.created_by.id) != str(user.id)

        item_data["supplier"] = supplier.name
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "supplier" in serializer.errors
        assert serializer.errors["supplier"] == ([
            f"Supplier '{supplier.name}' does not exist. "
             "Please create a new supplier if this is a new entry."
        ])

    def test_item_creation_variants_field_is_optional(self, user, item_data):
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert "variants" not in item_data
        assert serializer.is_valid()

        item = serializer.save()
        assert len(item.variants.all()) == 0

    def test_item_creation_with_valid_variants_field_format(
        self,
        user,
        item_data
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

        item_variants = item.variants.all()
        assert len(item_variants) == 2

        # Check item color variant and its options
        item_color_variant = item_variants.filter(name="Color").first()
        assert item_color_variant is not None

        item_color_variant_options = [
            option.body
            for option
            in item_color_variant.options.all()
        ]
        assert len(item_color_variant_options) == 2
        assert "red" in item_color_variant_options
        assert "blue" in item_color_variant_options

        # Check item size variant and its options
        item_size_variant = item_variants.filter(name="Size").first()
        assert item_size_variant is not None

        item_size_variant_options = [
            option.body
            for option
            in item_size_variant.options.all()
        ]
        assert len(item_size_variant_options) == 2
        assert "160kg" in item_size_variant_options
        assert "90kg" in item_size_variant_options

    def test_item_creation_fails_with_invalid_variants_json_string_format(
        self,
        user,
        item_data
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
        item_data["variants"] = variants
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert serializer.errors["variants"] == ["Not a valid string."]

    def test_item_creation_fails_with_malformed_json(self, user, item_data):
        item_data["variants"] = "{color}"
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] == ["Invalid JSON format for variants."]
        )

    def test_item_creation_fails_with_invalid_variants_structure(
        self,
        user,
        item_data
    ):
        variants = {
            "name": "Color",
            "options": ["red", "blue"]
        }

        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})
        
        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert serializer.errors["variants"] == ["Variants must be a list."]
    
    def test_item_creation_fails_with_invalid_variant_object_structure(
        self,
        user,
        item_data
    ):
        variants = ["Color", "Size"]
        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})

        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] ==
            ["Each variant must be an object with 'name' and 'options' as properties."]
        )
    
    def test_item_creation_fails_with_missing_variant_object_name(
        self,
        user,
        item_data
    ):
        variants = [
            {
                "options": ["red", "blue"]
            },
        ]

        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})
        
        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] ==
            ["Each variant must have a 'name'."]
        )
    
    def test_item_creation_fails_with_missing_variant_object_options(
        self,
        user,
        item_data
    ):
        variants = [
            {
                "name": "Color",
            },
        ]
        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})
        
        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] ==
            ["Each variant must have an 'options' list."]
        )
    
    def test_item_creation_fails_with_invalid_variant_options_structure(
        self,
        user,
        item_data
    ):
        variants = [
            {
                "name": "Color",
                "options": "red, blue"
            },
        ]
        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})
        
        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] ==
            ["Each variant must have an 'options' list."]
        )

    def test_item_creation_fails_with_duplicated_variant_name(
        self,
        user,
        item_data
    ):
        variants = [
            {
                "name": "Color",
                "options": ["red", "blue"]
            },
            {
                "name": "Color",
                "options": ["white", "black"]
            },
        ]
        item_data["variants"] = json.dumps(variants)
        serializer = ItemSerializer(data=item_data, context={'user': user})
        
        assert not serializer.is_valid()
        assert "variants" in serializer.errors
        assert (
            serializer.errors["variants"] ==
            ["Each variant name should be unique."]
        )
    
    def test_item_creation_picture_field_is_optional(self, user, item_data):
        assert "picture" not in item_data

        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()
        
        item = serializer.save()
        assert not item.picture
        assert item.picture.name is None
    
    def test_item_creation_with_valid_picture(
        self,
        user,
        item_data,
        setup_cleanup_picture
    ):
        item_data["picture"] = setup_cleanup_picture
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        assert item.picture is not None
        assert "item_small.gif" in item.picture.name
    
    def test_item_creation_fails_with_oversized_picture(
        self,
        user,
        item_data,
        small_gif
    ):
        item_data["picture"] = SimpleUploadedFile(
            "oversized.gif",
            small_gif * (2 * 1024 * 1024 + 1),
            content_type="image/gif"
        )
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert not serializer.is_valid()

        assert "picture" in serializer.errors
        assert serializer.errors["picture"] == ["Picture size must be less than 2MB."]
    
    def test_item_creation_fails_with_invalid_picture_file_type(
        self,
        user,
        item_data,
    ):
        item_data["picture"] = SimpleUploadedFile(
            "avatar.txt",
            b"not an image",
            content_type="text/plain"
        )
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert not serializer.is_valid()

        assert "picture" in serializer.errors
        assert serializer.errors["picture"] == [
            (
                "Upload a valid image. "
                "The file you uploaded was either "
                "not an image or a corrupted image."
            )
        ]
        assert serializer.errors["picture"][0].code == 'invalid_image'

    def test_item_serializer_data_fields(self, item):
        serializer = ItemSerializer(item)
        item_data = serializer.data

        assert "id" in item_data
        assert "created_by" in item_data
        assert "supplier" in item_data
        assert "category" in item_data
        assert "name" in item_data
        assert "quantity" in item_data
        assert "price" in item_data
        assert "total_price" in item_data
        assert "picture" in item_data
        assert "variants" in item_data
        assert "total_client_orders" in item_data
        assert 'total_supplier_orders' in item_data
        assert "in_inventory" in item_data
        assert "updated" in item_data
        assert "created_at" in item_data
        assert "updated_at" in item_data

    def test_item_serializer_data_fields_types(self, item, setup_cleanup_picture):
        item.picture = setup_cleanup_picture
        item.save()

        serializer = ItemSerializer(item)
        item_data = serializer.data

        assert type(item_data["id"]) == str
        assert type(item_data["created_by"]) == str
        assert type(item_data["supplier"]) == str
        assert type(item_data["category"]) == str
        assert type(item_data["name"]) == str
        assert type(item_data["quantity"]) == int
        assert type(item_data["price"]) == float
        assert type(item_data["total_price"]) == float
        assert type(item_data["variants"]) == list
        assert type(item_data["picture"]) == str
        assert type(item_data["total_client_orders"]) == int
        assert type(item_data["total_supplier_orders"]) == int
        assert type(item_data["in_inventory"]) == bool
        assert type(item_data["updated"]) == bool
        assert type(item_data["created_at"]) == str
        assert type(item_data["updated_at"]) == str

    def test_item_serializer_data_for_basic_fields(
        self,
        user,
        category,
        supplier,
    ):
        item_data = {
            "category": category.name,
            "supplier": supplier.name,
            "name": "Projector",
            "quantity": 2,
            "price": 199.99,
        }

        create_serializer = ItemSerializer(data=item_data, context={'user': user})
        assert create_serializer.is_valid()

        item = create_serializer.save()

        expected_data = {
            "created_by": user.username,
            "category": category.name,
            "supplier": supplier.name,
            "name": "Projector",
            "quantity": 2,
            "price": 199.99,
            "total_price": item_data["quantity"] * item_data["price"],
        }

        get_serializer = ItemSerializer(item)
        serializer_data = get_serializer.data

        assert serializer_data["id"] == item.id
        assert serializer_data["created_by"] == expected_data['created_by']
        assert serializer_data["supplier"] == expected_data['supplier']
        assert serializer_data["category"] == expected_data['category']
        assert serializer_data["name"] == expected_data['name']
        assert serializer_data["quantity"] == expected_data['quantity']
        assert serializer_data["price"] == expected_data['price']
        assert serializer_data["total_price"] == expected_data["total_price"]
    
    def test_item_serializer_data_for_picture_field(
        self,
        user,
        item_data,
        setup_cleanup_picture
    ):
        picture = setup_cleanup_picture
        item_data["picture"] = picture
        create_serializer = ItemSerializer(data=item_data, context={'user': user})
        assert create_serializer.is_valid()

        item = create_serializer.save()

        get_serializer = ItemSerializer(item)
        serializer_data = get_serializer.data

        assert serializer_data["picture"].endswith(picture.name)

    def test_item_serializer_data_for_variants_field(
        self,
        user,
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
        create_serializer = ItemSerializer(data=item_data, context={'user': user})
        assert create_serializer.is_valid()

        item = create_serializer.save()

        get_serializer = ItemSerializer(item)
        serializer_data = get_serializer.data

        assert serializer_data["variants"] == variants

    def test_item_serializer_data_for_timestamps_fields(self, user, item_data):
        create_serializer = ItemSerializer(data=item_data, context={'user': user})
        assert create_serializer.is_valid()

        item = create_serializer.save()

        get_serializer = ItemSerializer(item)
        serializer_data = get_serializer.data

        assert serializer_data["created_at"] == item.created_at.strftime('%d/%m/%Y')
        assert serializer_data["updated_at"] == item.updated_at.strftime('%d/%m/%Y')
    
    def test_item_serializer_data_for_boolean_fields(self, user, item_data):
        create_serializer = ItemSerializer(data=item_data, context={'user': user})
        assert create_serializer.is_valid()

        item = create_serializer.save()

        get_serializer = ItemSerializer(item)
        serializer_data = get_serializer.data

        assert serializer_data["in_inventory"] == True
        assert serializer_data["updated"] == False
    
    def test_item_creation_registers_a_new_activity(self, user, item_data):
        serializer = ItemSerializer(data=item_data, context={'user': user})
        assert serializer.is_valid()

        item = serializer.save()
        item_creation_activity = (
            Activity.objects.filter(
                action="created",
                model_name="item",
                object_ref__contains=[item.name]
            ).first()
        )

        assert item_creation_activity is not None

    def test_item_serializer_update(self, user, item_data):
        item = ItemFactory.create(
            created_by=user,
            name="Pack",
            quantity=4,
            price=299.50
        )

        item_initial_data = {
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price
        }

        serializer = ItemSerializer(item, data=item_data, context={'user': user})
        assert serializer.is_valid()

        item_update = serializer.save()
        assert item_update.updated

        assert item_update.name == "Projector"
        assert item_update.name != item_initial_data["name"]

        assert item_update.quantity == 2
        assert item_update.quantity != item_initial_data["quantity"]

        assert item_update.price == Decimal('199.99')
        assert item_update.price != item_initial_data["price"]
    
    def test_item_serializer_partial_update(self, user):
        item = ItemFactory.create(created_by=user, name="Pack")
        item_initial_name = item.name
        serializer = ItemSerializer(
            item,
            data={"name": "Projector"},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        item_update = serializer.save()
        assert item_update.updated

        assert item_update.name == "Projector"
        assert item_update.name != item_initial_name

    def test_item_update_removes_optional_field_if_set_to_none(self, user, supplier):
        item = ItemFactory.create(created_by=user, supplier=supplier)
        assert item.supplier is not None

        serializer = ItemSerializer(
            item,
            data={"supplier": None},
            context={"user": user},
            partial=True
        )
        assert serializer.is_valid()

        item_update = serializer.save()
        assert item_update.updated
        assert item.supplier is None
    
    def test_item_update_registers_a_new_activity(self, user, item_data):
        item = ItemFactory.create(created_by=user)
        serializer = ItemSerializer(item, data=item_data, context={'user': user})
        assert serializer.is_valid()

        item_update = serializer.save()

        item_creation_activity = (
            Activity.objects.filter(
                action="updated",
                model_name="item",
                object_ref__contains=[item_update.name]
            ).first()
        )

        assert item_creation_activity is not None
