import pytest
from django.utils.timezone import now, datetime
from django.db.utils import IntegrityError
from apps.base.models import User, Activity


@pytest.fixture
def user_instance(db):
    return User.objects.create_user(
        username="adel",
        first_name="Adil",
        last_name="El Bali",
        email="adxel.elb@gmail.com",
        password="adelelb159@"
    )

@pytest.fixture
def activity_instance(db, user_instance):
    return Activity.objects.create(
        user=user_instance,
        action="created",
        model_name="item",
        object_ref=["Headphones"]
    )


@pytest.mark.django_db
class TestUserModel:
    """Model Tests for the User Model"""

    def test_user_str_repr(self, user_instance):
        assert user_instance.__str__() == 'adel'
        assert user_instance.username == 'adel'

    def test_user_username(self, user_instance):
        assert user_instance.username == 'adel'

    def test_user_full_name(self, user_instance):
        full_name = "Adil El Bali"
        assert user_instance.get_full_name() == full_name

    def test_user_email_is_required(self):
        with pytest.raises(
            TypeError,
            match="missing 1 required positional argument: 'email'"):
            User.objects.create_user(
                username="adelux",
                first_name="Adil",
                last_name="El Bali",
                password="adelelb159@"
            )

    def test_user_password_is_required(self):
        with pytest.raises(
            ValueError,
            match="The Password field must be set"):
            User.objects.create_user(
                username="adelux",
                first_name="Adil",
                last_name="El Bali",
                email="adil.elb@gmail.com",
            )

    def test_user_username_is_unique(self, user_instance):
        with pytest.raises(IntegrityError, match='unique constraint'):
            User.objects.create_user(
                username="adel",
                first_name="Adil",
                last_name="El Bali",
                email="adil.elb@gmail.com",
                password="adelelb159@"
            )

    def test_user_email_is_unique(self, user_instance):
        with pytest.raises(IntegrityError, match='unique constraint'):
            User.objects.create_user(
                username="adelux",
                first_name="Adil",
                last_name="El Bali",
                email="adxel.elb@gmail.com",
                password="adelelb159@"
            )

    def test_user_invalid_email(self, user_instance):
        with pytest.raises(ValueError, match='Invalid email'):
            User.objects.create_user(
                username="adelux",
                first_name="Adil",
                last_name="El Bali",
                email="adxel.elbgmail.com",
                password="adelelb159@"
            )

    def test_user_auto_now_add_field(self, user_instance):
        assert user_instance.date_joined is not None
        assert isinstance(user_instance.date_joined, datetime)
        assert user_instance.date_joined <= now()
    
    def test_user_auto_now_field(self, user_instance):
        initial_updated_at = user_instance.updated_at
        user_instance.username = "adelux"
        user_instance.save()

        assert user_instance.updated_at is not None
        assert isinstance(user_instance.updated_at, datetime)
        assert user_instance.date_joined < user_instance.updated_at
        assert user_instance.updated_at <= now()
        assert user_instance.updated_at > initial_updated_at

    def test_user_one_to_many_activities(
        self,
        user_instance,
        activity_instance,
    ):
        second_activity = Activity.objects.create(
            user=user_instance,
            action="updated",
            model_name="item",
            object_ref=["Headphones"]
        )
        assert activity_instance.user == user_instance
        assert second_activity.user == user_instance


@pytest.mark.django_db
class TestActivityModel:
    """Model tests for the Activity Model"""

    def test_activity_str_repr(self, activity_instance, user_instance):
        expected_repr = (
            f"{user_instance.username} "
            f"{activity_instance.action} "
            f"{activity_instance.model_name} "
            f"{activity_instance.object_ref}"
        )
        assert activity_instance.__str__() == expected_repr
    
    def test_activity_user_is_required(self):
        with pytest.raises(IntegrityError,
                           match='"user_id" violates not-null constraint'):
            Activity.objects.create(
                action="deleted",
                model_name="item",
            )

    def test_activity_user_relationship(self, activity_instance, user_instance):
        assert activity_instance.user == user_instance

    def test_activity_many_to_one_user(self, activity_instance, user_instance):
        second_activity = Activity.objects.create(
            user=user_instance,
            action="deleted",
            model_name="item",
            object_ref=["Headphones", "Projectors"]
        )
        assert activity_instance.user == user_instance
        assert second_activity.user == user_instance

    def test_activity_object_ref_default_value(self, user_instance):
        activity = Activity.objects.create(
            user=user_instance,
            action="deleted",
            model_name="item",
        )
        assert hasattr(activity, 'object_ref')
        assert activity.object_ref == []

    def test_activity_object_ref_list(self, user_instance):
        activity = Activity.objects.create(
            user=user_instance,
            action="deleted",
            model_name="item",
            object_ref=["Headphones", "Projectors"]
        )
        assert activity.object_ref == ["Headphones", "Projectors"]
        assert hasattr(activity, 'object_ref')
        assert type(activity.object_ref) == list

    def test_activity_auto_now_add_field(self, activity_instance):
        assert activity_instance.created_at is not None
        assert isinstance(activity_instance.created_at, datetime)
        assert activity_instance.created_at <= now()
