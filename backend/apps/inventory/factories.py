import factory
from apps.base.factories import UserFactory
from .models import Category, Variant, Item, VariantOption


class CategoryFactory(factory.django.DjangoModelFactory):
    """Category Factory"""
    class Meta:
        model = Category
    
    created_by = factory.SubFactory(UserFactory)
    name = factory.Faker("word")


class VariantFactory(factory.django.DjangoModelFactory):
    """Variant Factory"""
    class Meta:
        model = Variant
    
    created_by = factory.SubFactory(UserFactory)
    name = factory.Faker("word")


class ItemFactory(factory.django.DjangoModelFactory):
    """Item Factory"""
    class Meta:
        model = Item
        skip_postgeneration_save = True

    created_by = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    supplier = factory.SubFactory("apps.supplier_orders.factories.SupplierFactory")
    name = factory.Sequence(lambda n: f"item_{n}")
    quantity = factory.Faker("pyint", min_value=2, max_value=20)
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        max_value=999.99,
        min_value=1,
    )

    @factory.post_generation
    def variants(self, create, extracted, **kwargs):
        """Handle ManyToMany relationships after Item is created."""
        # Check whether the item object is saved to the database
        if not create:
            return

        if extracted:
            # If a list of variants is provided, add them to the item
            self.variants.add(*extracted)

        else:
            # Otherwise, create 3 variants by default and link them
            variants = VariantFactory.create_batch(3)
            self.variants.add(*variants)


class VariantOptionFactory(factory.django.DjangoModelFactory):
    """VarianOption Factory"""
    class Meta:
        model = VariantOption
    
    item = factory.SubFactory(ItemFactory)
    variant = factory.SubFactory(VariantFactory)
    body = factory.Faker("word")
