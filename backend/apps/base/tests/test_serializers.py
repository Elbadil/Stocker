import pytest
from apps.base.models import User, Activity
from apps.base.serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserLoginSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ActivitySerializer
)


@pytest.fixture
def user_instance():
    user = User(
        username="adel",
        first_name="Adil",
        last_name="El Bali",
        email="adxel.elb@gmail.com",
        bio="Backend Developer"
    )
    user.set_password("adeltest123@")
    return user

@pytest.fixture
def user_serializer(db, user_instance):
    user_instance.save()
    return UserSerializer(user_instance)

@pytest.fixture
def user_register_serializer_data(user_instance):
    return {
        "username": user_instance.username,
        "first_name": user_instance.first_name,
        "last_name": user_instance.last_name,
        "email": user_instance.email,
        "password1": "adeltest123@",
        "password2": "adeltest123@"
    }

@pytest.fixture
def user_login_serializer_data(user_instance):
    return {
        "email": user_instance.email,
        "password": "adeltest123@",
    }

@pytest.fixture
def change_password_serializer_data():
    return {
        "old_password": "adeltest123@",
        "new_password1": "adlux567@",
        "new_password2": "adlux567@"
    }

@pytest.fixture
def reset_password_serializer_data(change_password_serializer_data):
    data = change_password_serializer_data.copy()
    data.pop("old_password")
    return data

@pytest.fixture
def activity_instance(user_instance, user_serializer):
    return Activity(
        user=user_instance,
        action="created",
        model_name="item",
        object_ref=["Headphones"]
    )

@pytest.fixture
def activity_serializer(activity_instance):
    activity_instance.save()
    return ActivitySerializer(activity_instance)


@pytest.mark.django_db
class TestUserSerializer:
    """Tests for the UserSerializer"""

    def test_user_serializer_model(self, user_serializer):
        assert isinstance(user_serializer.instance, User)

    def test_user_serializer_fields(self, user_serializer):
        user_data = user_serializer.data
        assert 'id' in user_data
        assert 'username' in user_data
        assert 'first_name' in user_data
        assert 'last_name' in user_data
        assert 'email' in user_data
        assert 'avatar' in user_data
        assert 'bio' in user_data
    
    def test_user_serializer_fields_data_type(self, user_serializer):
        user_data = user_serializer.data
        assert isinstance(user_data['id'], str)
        assert isinstance(user_data['username'], str)
        assert isinstance(user_data['first_name'], str)
        assert isinstance(user_data['last_name'], str)
        assert isinstance(user_data['email'], str)
        assert isinstance(user_data['bio'], str)

    def test_user_serializer_data(self, user_serializer):
        expected_user_data = {
            "username": "adel",
            "first_name": "Adil",
            "last_name": "El Bali",
            "email": "adxel.elb@gmail.com",
            "avatar": None,
            "bio": "Backend Developer"
        }
        assert user_serializer.data['username'] == expected_user_data['username']
        assert user_serializer.data['first_name'] == expected_user_data['first_name']
        assert user_serializer.data['last_name'] == expected_user_data['last_name']
        assert user_serializer.data['email'] == expected_user_data['email']
        assert user_serializer.data['avatar'] == expected_user_data['avatar']
        assert user_serializer.data['bio'] == expected_user_data['bio']


@pytest.mark.django_db
class TestUserRegisterSerializer:
    """Tests for UserRegisterSerializer"""

    def test_user_register_successful_registration(self, user_register_serializer_data):
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.username == "adel"
        assert user.first_name == "Adil"
        assert user.last_name == "El Bali"
        assert user.email == "adxel.elb@gmail.com"

    def test_user_register_username_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('username')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "username" in serializer.errors
        assert serializer.errors["username"] == ["This field is required."]
    
    def test_user_register_first_name_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('first_name')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "first_name" in serializer.errors
        assert serializer.errors["first_name"] == ["This field is required."]
    
    def test_user_register_last_name_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('last_name')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "last_name" in serializer.errors
        assert serializer.errors["last_name"] == ["This field is required."]
    
    def test_user_register_email_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('email')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert serializer.errors["email"] == ["This field is required."]
    
    def test_user_register_password1_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('password1')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "password1" in serializer.errors
        assert serializer.errors["password1"] == ["This field is required."]
    
    def test_user_register_password2_is_required(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data.pop('password2')
        serializer = UserRegisterSerializer(data=user_register_serializer_data)

        assert not serializer.is_valid()
        assert "password2" in serializer.errors
        assert serializer.errors["password2"] == ["This field is required."]

    def test_user_register_username_is_unique(
        self,
        user_register_serializer_data,
        user_serializer
    ):
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "username" in serializer.errors
        assert serializer.errors["username"] == ["user with this username already exists."]

    def test_user_register_email_is_unique(
        self,
        user_register_serializer_data,
        user_serializer
    ):
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert serializer.errors["email"] == ["user with this email already exists."]

    def test_user_register_invalid_email(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["email"] = "adel.com"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert serializer.errors["email"] == ["Enter a valid email address."]

    def test_user_register_mismatched_passwords(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["password1"] = "adeltest123"
        user_register_serializer_data["password2"] = "deltest123"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert serializer.errors["password"] == ["The two password fields do not match."]

    def test_user_register_invalid_short_password(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["password1"] = "128abc"
        user_register_serializer_data["password2"] = "128abc"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert (
            serializer.errors["password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_user_register_invalid_numeric_password(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["password1"] = "14958373"
        user_register_serializer_data["password2"] = "14958373"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert serializer.errors["password"] == ["This password is entirely numeric."]

    def test_user_register_invalid_common_password(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["password1"] = "abc12345"
        user_register_serializer_data["password2"] = "abc12345"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert serializer.errors["password"] == ["This password is too common."]

    def test_user_register_invalid_similar_to_user_attribute_password(
        self,
        user_register_serializer_data
    ):
        user_register_serializer_data["password1"] = "elbali12"
        user_register_serializer_data["password2"] = "elbali12"
        serializer = UserRegisterSerializer(data=user_register_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert (
            serializer.errors["password"] ==
            ["The password is too similar to the last name."]
        )


@pytest.mark.django_db
class TestUserLoginSerializer:
    """Tests for UserLoginSerializer"""

    def test_user_login_successful_login(
        self,
        user_login_serializer_data,
        user_serializer
    ):
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert serializer.is_valid()

    def test_user_login_validated_data_contains_authenticated_user(
        self,
        user_login_serializer_data,
        user_serializer
    ):
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert serializer.is_valid()
        user = serializer.validated_data["user"]
        assert user.username == "adel"
        assert user.first_name == "Adil"
        assert user.last_name == "El Bali"
        assert user.email == "adxel.elb@gmail.com"

    def test_user_login_authentication_after_successful_login(
        self,
        user_login_serializer_data,
        user_serializer
    ):
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert serializer.is_valid()
        user = serializer.validated_data["user"]
        assert user.is_authenticated

    def test_user_login_unsuccessful_login(
        self,
        user_serializer
    ):
        incorrect_login_data = {
            "email": "elbaliadil@gmail.com",
            "password": "incorrectPassword"
        }
        serializer = UserLoginSerializer(data=incorrect_login_data)
        assert not serializer.is_valid()
        assert "error" in serializer.errors
        assert serializer.errors["error"][0].startswith("Login Unsuccessful.")

    def test_user_login_email_is_required(self, user_login_serializer_data):
        user_login_serializer_data.pop('email')
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert serializer.errors["email"] == ["This field is required."]

    def test_user_login_password_is_required(self, user_login_serializer_data):
        user_login_serializer_data.pop('password')
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors
        assert serializer.errors["password"] == ["This field is required."]

    def test_user_login_email_does_not_exist(
        self,
        user_login_serializer_data,
        user_serializer
    ):
        user_login_serializer_data["email"] = "elbaliadil@gmail.com"
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert not serializer.is_valid()
        assert "error" in serializer.errors
        assert serializer.errors["error"][0].startswith("Login Unsuccessful.")

    def test_user_login_incorrect_password(
        self,
        user_login_serializer_data,
        user_serializer
    ):
        user_login_serializer_data["password"] = "incorrectPassword"
        serializer = UserLoginSerializer(data=user_login_serializer_data)
        assert not serializer.is_valid()
        assert "error" in serializer.errors
        assert serializer.errors["error"][0].startswith("Login Unsuccessful.")


@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Tests for ChangePasswordSerializer"""

    def test_successful_pwd_change(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password(change_password_serializer_data["new_password1"])
        assert not user.check_password(change_password_serializer_data["old_password"])

    def test_change_pwd_old_password_is_required(
        self,
        change_password_serializer_data
    ):
        change_password_serializer_data.pop('old_password')
        serializer = ChangePasswordSerializer(data=change_password_serializer_data)
        assert not serializer.is_valid()
        assert "old_password" in serializer.errors
        assert serializer.errors["old_password"] == ["This field is required."]

    def test_change_pwd_new_password1_is_required(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data.pop('new_password1')
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password1" in serializer.errors
        assert serializer.errors["new_password1"] == ["This field is required."]

    def test_change_pwd_new_password2_is_required(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data.pop('new_password2')
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password2" in serializer.errors
        assert serializer.errors["new_password2"] == ["This field is required."]

    def test_change_pwd_incorrect_old_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["old_password"] = "incorrectOldPassword"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "old_password" in serializer.errors
        assert serializer.errors["old_password"] == ["Old password is incorrect."]

    def test_change_pwd_new_password_similar_to_the_old_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "adeltest123@"
        change_password_serializer_data["new_password2"] = "adeltest123@"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["New password cannot be the same as the old password."]
        )

    def test_change_pwd_mismatched_new_passwords(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "adlux567@"
        change_password_serializer_data["new_password2"] = "adlux57@@"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["The two new password fields do not match."]
        )

    def test_change_pwd_invalid_short_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "128abc"
        change_password_serializer_data["new_password2"] = "128abc"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_change_pwd_invalid_numeric_new_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "14958373"
        change_password_serializer_data["new_password2"] = "14958373"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["This password is entirely numeric."]
        )

    def test_change_pwd_invalid_common_new_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "abc12345"
        change_password_serializer_data["new_password2"] = "abc12345"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert serializer.errors["new_password"] == ["This password is too common."]

    def test_change_pwd_invalid_similar_to_user_attribute_new_password(
        self,
        change_password_serializer_data,
        user_instance,
        user_serializer
    ):
        change_password_serializer_data["new_password1"] = "elbali12"
        change_password_serializer_data["new_password2"] = "elbali12"
        serializer = ChangePasswordSerializer(
            user=user_instance,
            data=change_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["The password is too similar to the last name."]
        )


class TestResetPasswordSerializer:
    """Tests for the ResetPasswordSerializer"""

    def test_successful_pwd_reset(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password(reset_password_serializer_data["new_password1"])

    def test_reset_pwd_new_password1_is_required(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data.pop('new_password1')
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password1" in serializer.errors
        assert serializer.errors["new_password1"] == ["This field is required."]

    def test_reset_pwd_new_password2_is_required(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data.pop('new_password2')
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password2" in serializer.errors
        assert serializer.errors["new_password2"] == ["This field is required."]

    def test_reset_pwd_mismatched_new_passwords(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data["new_password1"] = "adlux567@"
        reset_password_serializer_data["new_password2"] = "adlux57@@"
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["The two new password fields do not match."]
        )

    def test_reset_pwd_invalid_short_password(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data["new_password1"] = "128abc"
        reset_password_serializer_data["new_password2"] = "128abc"
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_reset_pwd_invalid_numeric_new_password(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data["new_password1"] = "14958373"
        reset_password_serializer_data["new_password2"] = "14958373"
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["This password is entirely numeric."]
        )

    def test_reset_pwd_invalid_common_new_password(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data["new_password1"] = "abc12345"
        reset_password_serializer_data["new_password2"] = "abc12345"
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert serializer.errors["new_password"] == ["This password is too common."]

    def test_reset_pwd_invalid_similar_to_user_attribute_new_password(
        self,
        reset_password_serializer_data,
        user_instance,
        user_serializer
    ):
        reset_password_serializer_data["new_password1"] = "elbali12"
        reset_password_serializer_data["new_password2"] = "elbali12"
        serializer = ResetPasswordSerializer(
            user=user_instance,
            data=reset_password_serializer_data
        )
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert (
            serializer.errors["new_password"] ==
            ["The password is too similar to the last name."]
        )


class TestActivitySerializer:
    """Tests for the ActivitySerializer"""

    def test_activity_serializer_model(self, activity_serializer):
        assert isinstance(activity_serializer.instance, Activity)
    
    def test_activity_serializer_fields(self, activity_serializer):
        activity_data = activity_serializer.data
        assert "id" in activity_data
        assert "user" in activity_data
        assert "action" in activity_data
        assert "model_name" in activity_data
        assert "object_ref" in activity_data
        assert "created_at" in activity_data

    def test_activity_serializer_fields_data_type(self, activity_serializer):
        activity_data = activity_serializer.data
        assert isinstance(activity_data['id'], str)
        assert isinstance(activity_data['user'], dict)
        assert isinstance(activity_data['action'], str)
        assert isinstance(activity_data['model_name'], str)
        assert isinstance(activity_data['object_ref'], list)
        assert isinstance(activity_data['created_at'], str)

    def test_activity_serializer_data(self, activity_serializer):
        expected_activity_data = {
            "user": {
                "username": "adel",
                "avatar": None
            },
            "action": "created",
            "model_name": "item",
            "object_ref": ["Headphones"]
        }
        assert activity_serializer.data['user'] == expected_activity_data['user']
        assert activity_serializer.data['action'] == expected_activity_data['action']
        assert activity_serializer.data['model_name'] == expected_activity_data['model_name']
        assert activity_serializer.data['object_ref'] == expected_activity_data['object_ref']
