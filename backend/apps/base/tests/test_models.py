import pytest
from django.db.utils import IntegrityError
from apps.base.models import User


@pytest.fixture
def user_instance(db):
    return User.objects.create_user(
        username="adel",
        first_name="Adil",
        last_name="El Bali",
        email="adxel.elb@gmail.com",
        password="adelelb159@"
    )


@pytest.mark.django_db
class TestUserModel:
    """Model Tests for the User Model"""

    def test_user_str_repr(self, user_instance):
        assert user_instance.__str__() == 'adel'
        assert user_instance.username == 'adel'

    def test_username(self, user_instance):
        assert user_instance.username == 'adel'

    def test_full_name(self, user_instance):
        full_name = "Adil El Bali"
        print(user_instance.get_full_name())
        assert user_instance.get_full_name() == full_name

    def test_username_uniqueness(self, user_instance):
        with pytest.raises(IntegrityError, match='unique constraint'):
            User.objects.create_user(
                username="adel",
                first_name="Adil",
                last_name="El Bali",
                email="adil.elb@gmail.com",
                password="adelelb159@"
            )

    def test_email_uniqueness(self, user_instance):
        with pytest.raises(IntegrityError, match='unique constraint'):
            User.objects.create_user(
                username="adelux",
                first_name="Adil",
                last_name="El Bali",
                email="adxel.elb@gmail.com",
                password="adelelb159@"
            )
