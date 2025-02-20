import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from apps.inventory.factories import CategoryFactory, ItemFactory
from apps.inventory.models import Category, Item


# @pytest.fixture
# def user(db):
# 	return UserFactory.create()

# @pytest.fixture
# def supplier(db, user):
#     return SupplierFactory.create(created_by=user)

@pytest.fixture
def category(db):
    return CategoryFactory.create()

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

    