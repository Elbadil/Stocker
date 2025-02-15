import factory
from faker import Faker
from .models import Activity


fake = Faker()


class ActivityFactory(factory.django.DjangoModelFactory):
    """Activity Factory"""
    class Meta:
        model = Activity
    
    action = factory.Iterator(["created", "updated", "deleted"])
    model_name = factory.Iterator(
        [
            "item",
            "client order",
            "sale",
            "supplier order"
        ]
    )
    object_ref = factory.LazyFunction(lambda: [fake.word() for _ in range(4)])
