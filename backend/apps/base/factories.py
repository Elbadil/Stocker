import factory
from faker import Faker
from django.contrib.auth.hashers import make_password
from .models import User, Activity


fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """User Factory"""
    class Meta:
        model = User
        skip_postgeneration_save = True

    # Increments every time we call the Factory
    username = factory.Sequence(lambda n: f"user_{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    # LazyAttribute has access to the obj and its attributes
    # and it requires a function to be executed
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    # Search for user's set_password and execute it with the passed arg "pw"
    password = factory.LazyFunction(lambda: make_password("pw"))
    bio = factory.Faker("sentence", nb_words=10)


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
