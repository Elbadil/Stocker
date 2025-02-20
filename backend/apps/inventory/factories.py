import factory
from apps.base.factories import UserFactory
from apps.supplier_orders.factories import SupplierFactory
from .models import Category, Item


class CategoryFactory(factory.django.DjangoModelFactory):
    """Category Factory"""
    class Meta:
        model = Category
    
    created_by = factory.SubFactory(UserFactory)
    name = factory.Faker("word")


class ItemFactory(factory.django.DjangoModelFactory):
    """Item Factory"""
    class Meta:
        model = Item
    
    category = factory.SubFactory(CategoryFactory)
    supplier = factory.SubFactory(SupplierFactory)
    name = factory.Faker("word")
    quantity = factory.Faker("pyint", min_value=1, max_value=20)
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=999.99,
        min_value=1,
    )
