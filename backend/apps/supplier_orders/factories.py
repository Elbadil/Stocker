import factory
from .models import Supplier


class SupplierFactory(factory.django.DjangoModelFactory):
    """Supplier Factory"""
    class Meta:
        model = Supplier

    name = factory.Faker("name")
    phone_number = factory.Faker("phone_number")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.name.replace(' ', '.').lower()}@example.com"
    )
