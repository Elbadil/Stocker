import pytest
import os
import jwt
import shutil
from django.conf import settings
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from datetime import datetime, timezone, timedelta
from apps.base.models import User


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_data():
    return {
        "username": "adel",
        "first_name": "Adil",
        "last_name": "El Bali",
        "email": "adxel.elb@gmail.com",
        "password": "adeltest123@"
    }

@pytest.fixture
def user_instance(db, user_data):
    return User.objects.create_user(**user_data)

@pytest.fixture
def expected_user_data(user_data):
    return {
        "username": user_data['username'],
        "first_name": user_data['first_name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "avatar": None,
        "bio": None
    }

@pytest.fixture
def update_user_data():
    return {
        "username": "adelux",
        "first_name": "Adel",
        "last_name": "Elb",
        "bio": "Backend Dev"
    }

@pytest.fixture
def setup_cleanup_avatar(user_instance):
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )
    avatar = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')

    yield avatar

    user_instance.refresh_from_db()
    user_image_folder = os.path.join(
        settings.MEDIA_ROOT,
        f"base/images/user/{user_instance.id}"
    )
    if os.path.exists(user_image_folder):
        shutil.rmtree(user_image_folder)

@pytest.fixture
def login_credentials(user_data):
    return {
        "email": user_data["email"],
        "password": user_data["password"]
    }

@pytest.fixture
def login_url():
    return reverse('login')

@pytest.fixture
def login_user(api_client, user_instance, login_url, login_credentials):
    res = api_client.post(
        login_url,
        login_credentials,
        format='json',
    )
    return res

@pytest.fixture
def access_token(login_user):
    login_res = login_user
    return login_res.data['access_token']

@pytest.fixture
def auth_client(api_client, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client

@pytest.fixture
def signup_view_data(user_data):
    return {
        "username": user_data['username'],
        "first_name": user_data['first_name'],
        "last_name": user_data['last_name'],
        "email": user_data['email'],
        "password1": "adeltest123@",
        "password2": "adeltest123@"
    }

@pytest.fixture
def signup_url():
    return reverse('register')

@pytest.fixture
def token_refresh_url():
    return reverse('token_refresh')

@pytest.fixture
def logout_url():
    return reverse('logout')

@pytest.fixture
def get_update_user_url():
    return reverse('get_update_user')


@pytest.mark.django_db
class TestLoginView:
    """Tests for LoginView"""

    def test_login_view_allowed_http_methods(
        self,
        api_client,
        login_url,
        login_credentials,
        user_instance
    ):
        get_res = api_client.get(
            login_url,
            format='json'
        )
        assert get_res.status_code == 405
        assert get_res.data["detail"] == 'Method \"GET\" not allowed.'

        post_res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert post_res.status_code == 200

        put_res = api_client.put(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'

        delete_res = api_client.delete(
            login_url,
            format='json'
        )
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

        options_res = api_client.options(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert options_res.status_code == 200

    def test_login_view_with_invalid_data(
        self,
        api_client,
        login_url,
        user_instance
    ):
        invalid_login_data = {
            "email": "elbaliadil@gmail.com",
            "password": "incorrectPassword"
        }
        res = api_client.post(
            login_url,
            data=invalid_login_data,
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_email_is_required_in_request_data(
        self,
        api_client,
        login_url,
        login_credentials
    ):
        login_credentials.pop('email')
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["This field is required."]
    
    def test_login_view_password_is_required_in_request_data(
        self,
        api_client,
        login_url,
        login_credentials
    ):
        login_credentials.pop('password')
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["This field is required."]

    def test_login_view_with_inexistent_email(
        self,
        api_client,
        login_url,
        login_credentials
    ):
        login_credentials["email"] = "elbaliadil@gmail.com"
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_with_incorrect_password(
        self,
        api_client,
        login_url,
        login_credentials
    ):
        login_credentials["password"] = "incorrectPassword"
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_with_valid_data(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200

    def test_user_is_authenticated_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated

    def test_access_token_in_response_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials,
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "access_token" in res.data
    
    def test_valid_access_token_in_response_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials,
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "access_token" in res.data

        access_token = res.data["access_token"]
        verify_token_url = reverse('token_verify')
        verify_res = api_client.post(
            verify_token_url,
            data={'token': access_token}
        )

        assert verify_res.status_code == 200

    def test_user_in_response_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials,
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "user" in res.data
    
    def test_expected_user_fields_in_response_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "user" in res.data

        user = res.data["user"]
        assert "id" in user
        assert "username" in user
        assert "first_name" in user
        assert "last_name" in user
        assert "email" in user
        assert "avatar" in user
        assert "bio" in user

    def test_expected_user_data_in_response_after_login(
        self,
        api_client,
        user_instance,
        expected_user_data,
        login_url,
        login_credentials
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "user" in res.data

        user = res.data["user"]
        assert user["username"] == expected_user_data["username"]
        assert user["first_name"] == expected_user_data["first_name"]
        assert user["last_name"] == expected_user_data["last_name"]
        assert user["email"] == expected_user_data["email"]
        assert user["avatar"] == expected_user_data["avatar"]
        assert user["bio"] == expected_user_data["bio"]

    def test_refresh_token_is_set_in_cookies_after_login(
        self,
        api_client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert res.cookies.get("refresh_token") is not None


@pytest.mark.django_db
class TestSignUpView:
    """Tests for SignUpView"""

    def test_signup_view_allowed_http_methods(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        get_res = api_client.get(
            signup_url,
            format='json'
        )
        assert get_res.status_code == 405
        assert get_res.data["detail"] == 'Method \"GET\" not allowed.'

        post_res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert post_res.status_code == 201

        put_res = api_client.put(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'

        delete_res = api_client.delete(
            signup_url,
            format='json'
        )
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

        options_res = api_client.options(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert options_res.status_code == 200

    def test_signup_view_username_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('username')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["This field is required."]
    
    def test_signup_view_first_name_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('first_name')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "first_name" in res.data
        assert res.data["first_name"] == ["This field is required."]

    def test_signup_view_last_name_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('last_name')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "last_name" in res.data
        assert res.data["last_name"] == ["This field is required."]
    
    def test_signup_view_email_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('email')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["This field is required."]
    
    def test_signup_view_password1_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('password1')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password1" in res.data
        assert res.data["password1"] == ["This field is required."]
    
    def test_signup_view_password2_is_required_in_request_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('password2')
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password2" in res.data
        assert res.data["password2"] == ["This field is required."]

    def test_signup_view_username_is_unique(
        self,
        api_client,
        signup_url,
        signup_view_data,
        user_instance
    ):
        signup_view_data['username'] = 'adel'
        signup_view_data['email'] = 'adxel.elbali@gmail.com'
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["user with this username already exists."]
    
    def test_signup_view_email_is_unique(
        self,
        api_client,
        signup_url,
        signup_view_data,
        user_instance
    ):
        signup_view_data['username'] = 'adxel'
        signup_view_data['email'] = 'adxel.elb@gmail.com'
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["user with this email already exists."]
    
    def test_signup_view_with_invalid_email(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data['email'] = 'adel.com'
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["Enter a valid email address."]

    def test_signup_view_with_mismatched_passwords(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "adeltest123"
        signup_view_data["password2"] = "deltest123"
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["The two password fields do not match."]
    
    def test_signup_view_with_invalid_short_password(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "128abc"
        signup_view_data["password2"] = "128abc"
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert (
            res.data["password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_signup_view_with_invalid_numeric_password(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "14958373"
        signup_view_data["password2"] = "14958373"
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["This password is entirely numeric."]

    def test_signup_view_with_invalid_similar_to_user_attribute_password(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "elbali12"
        signup_view_data["password2"] = "elbali12"
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["The password is too similar to the last name."]
    
    def test_signup_view_with_valid_data(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201

    def test_access_token_in_response_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "access_token" in res.data
    
    def test_valid_access_token_in_response_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "access_token" in res.data

        access_token = res.data["access_token"]
        verify_token_url = reverse('token_verify')
        verify_res = api_client.post(
            verify_token_url,
            data={'token': access_token}
        )

        assert verify_res.status_code == 200

    def test_user_in_response_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "user" in res.data
    
    def test_user_fields_in_response_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "user" in res.data

        user = res.data['user']
        assert 'id' in user
        assert 'username' in user
        assert 'first_name' in user
        assert 'last_name' in user
        assert 'email' in user
        assert 'avatar' in user
        assert 'bio' in user
    
    def test_expected_user_data_in_response_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
        expected_user_data
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "user" in res.data

        user = res.data['user']
        assert user['username'] == expected_user_data['username']
        assert user['first_name'] == expected_user_data['first_name']
        assert user['last_name'] == expected_user_data['last_name']
        assert user['email'] == expected_user_data['email']
        assert user['avatar'] == expected_user_data['avatar']
        assert user['bio'] == expected_user_data['bio']

    def test_user_is_authenticated_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data,
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert "user" in res.data

        user = User.objects.get(id=res.data["user"]["id"])
        assert user.is_authenticated

    def test_refresh_token_is_set_in_cookies_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert res.cookies.get("refresh_token") is not None

        user = User.objects.get(id=res.data['user']['id'])
        assert user.is_authenticated

    def test_confirmation_email_after_signup(
        self,
        api_client,
        signup_url,
        signup_view_data
    ):
        res = api_client.post(
            signup_url,
            data=signup_view_data,
            format='json'
        )
        assert res.status_code == 201
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.from_email == "elbadil.testing@gmail.com"
        assert email.to == ['adxel.elb@gmail.com']
        assert email.subject == "Welcome to Stocker"
        assert email.body == "You have Successfully Created A Stocker Account."


@pytest.mark.django_db
class TestCustomTokenRefreshView:
    """Tests for CustomTokenRefreshView"""

    def test_refresh_view_successful_token_refresh(
        self,
        auth_client,
        token_refresh_url
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200

    def test_access_token_in_response_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "access_token" in res.data
    
    def test_valid_access_token_in_response_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "access_token" in res.data

        access_token = res.data["access_token"]
        verify_token_url = reverse('token_verify')
        verify_res = auth_client.post(
            verify_token_url,
            data={'token': access_token}
        )

        assert verify_res.status_code == 200

    def test_user_in_response_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "user" in res.data

    def test_user_fields_in_response_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "user" in res.data

        user = res.data['user']
        assert 'id' in user
        assert 'username' in user
        assert 'first_name' in user
        assert 'last_name' in user
        assert 'email' in user
        assert 'avatar' in user
        assert 'bio' in user

    def test_user_data_in_response_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
        expected_user_data
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "user" in res.data

        user = res.data['user']
        assert user['username'] == expected_user_data['username']
        assert user['first_name'] == expected_user_data['first_name']
        assert user['last_name'] == expected_user_data['last_name']
        assert user['email'] == expected_user_data['email']
        assert user['avatar'] == expected_user_data['avatar']
        assert user['bio'] == expected_user_data['bio']

    def test_new_access_token_after_token_refresh(
        self,
        auth_client,
        access_token,
        token_refresh_url,
    ):
        token_before_refresh = access_token
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "access_token" in res.data

        # Get new access token
        token_after_refresh = res.data["access_token"]

        assert token_before_refresh != token_after_refresh
    
    def test_valid_new_access_token_after_token_refresh(
        self,
        auth_client,
        token_refresh_url,
    ):
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 200
        assert "access_token" in res.data

        access_token = res.data["access_token"]
        verify_token_url = reverse('token_verify')
        verify_res = auth_client.post(
            verify_token_url,
            data={'token': access_token}
        )

        assert verify_res.status_code == 200
    
    def test_refresh_token_fails_with_expired_token(
        self,
        api_client,
        user_instance,
        token_refresh_url
    ):
        # Create expired refresh token for the user
        refresh_token = RefreshToken.for_user(user_instance)
        exp_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        refresh_token['exp'] = int(exp_time.timestamp())
        refresh_token['token_version'] = 1
        api_client.cookies['refresh_token'] = refresh_token

        # Send token refresh request
        res = api_client.post(token_refresh_url)

        assert res.status_code == 401
        assert "error" in res.data
        assert res.data["error"] == "Invalid or expired token."

    def test_refresh_token_missing_from_request_cookies(
        self,
        api_client,
        token_refresh_url
    ):
        res = api_client.post(token_refresh_url)
        assert res.status_code == 401
        assert "error" in res.data
        assert res.data["error"] == "No refresh_token found in cookies."

    def test_refresh_view_with_invalid_user_token_version(
        self,
        auth_client,
        user_instance,
        token_refresh_url
    ):
        # Change user token version
        user_instance.token_version = 2
        user_instance.save()

        # Get refresh token version
        refresh_token = RefreshToken(auth_client.cookies.get('refresh_token').value)
        refresh_token_version = refresh_token.payload['token_version']

        # Send token refresh request
        res = auth_client.post(token_refresh_url)

        assert res.status_code == 401
        assert refresh_token_version != user_instance.token_version
        assert "error" in res.data
        assert res.data["error"] == "Invalid or expired token."

    def test_refresh_view_with_invalid_refresh_token(
        self,
        auth_client,
        token_refresh_url,
    ):
        auth_client.cookies.clear()
        auth_client.cookies["refresh_token"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 401
        assert "error" in res.data
        assert res.data["error"] == "Invalid or expired token."

    def test_refresh_view_with_inexistent_user(
        self,
        auth_client,
        token_refresh_url
    ):
        # Change refresh token's user_id
        refresh_token = RefreshToken(auth_client.cookies.get('refresh_token').value)
        refresh_token['user_id'] = "1473a840-d123-41f0-91d5-e16e0ff0c6c3"
        auth_client.cookies["refresh_token"] = str(refresh_token)

        # Send token refresh request
        res = auth_client.post(token_refresh_url)
        assert res.status_code == 401
        assert "error" in res.data
        assert res.data["error"] == "Invalid or expired token."


@pytest.mark.django_db
class TestLogoutView:
    """Tests for LogoutView"""

    def test_logout_view_successful_logout(
        self,
        auth_client,
        logout_url
    ):
        res = auth_client.post(logout_url)
        assert res.status_code == 204
        assert res.data["message"] == "User has successfully logged out."

    def test_blacklist_refresh_token_after_logout(
        self,
        auth_client,
        logout_url
    ):
        res = auth_client.post(logout_url)
        refresh_token = res.cookies.get('refresh_token').value
        assert res.status_code == 204
        assert res.data["message"] == "User has successfully logged out."
        with pytest.raises(TokenError, match='Token is invalid or expired'):
            RefreshToken(refresh_token)

    def test_refresh_token_deletion_after_logout(
        self,
        auth_client,
        logout_url
    ):
        # Get the initial refresh token value
        initial_token = auth_client.cookies.get('refresh_token')
        assert initial_token is not None
        assert len(initial_token.value) > 1

        # Send logout request
        res = auth_client.post(logout_url)

        # Ensure status code and message are correct
        assert res.status_code == 204
        assert res.data["message"] == "User has successfully logged out."

        # Check that the refresh token cookie is "emptied"
        after_logout_token = auth_client.cookies.get('refresh_token')
        assert after_logout_token.value != initial_token.value
        assert after_logout_token.value == ""

    def test_refresh_token_missing_from_request_cookies(
        self,
        auth_client,
        logout_url
    ):
        auth_client.cookies.clear()
        res = auth_client.post(logout_url)
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "No refresh token found."
    
    def test_logout_view_with_invalid_refresh_token(
        self,
        auth_client,
        logout_url
    ):
        auth_client.cookies["refresh_token"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        res = auth_client.post(logout_url)
        assert res.status_code == 403
        assert "error" in res.data
        assert res.data["error"] == "Token is invalid or expired"

    def test_logout_view_authentication_is_required(
        self,
        api_client,
        logout_url
    ):
        res = api_client.post(logout_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."
    
    def test_logout_view_with_invalid_access_token(
        self,
        auth_client,
        logout_url,
    ):
        auth_client.credentials(
            HTTP_AUTHORIZATION=
            f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        )
        res = auth_client.post(logout_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Given token not valid for any token type"
        assert res.data["messages"][0]["message"] == "Token is invalid or expired"

    def test_logout_view_allowed_http_methods(
        self,
        auth_client,
        logout_url,
    ):
        get_res = auth_client.get(logout_url)
        assert get_res.status_code == 405
        assert get_res.data["detail"] == 'Method \"GET\" not allowed.'

        post_res = auth_client.post(logout_url)
        assert post_res.status_code == 204

        put_res = auth_client.put(logout_url)
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'

        delete_res = auth_client.delete(logout_url)
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

        options_res = auth_client.options(logout_url)
        assert options_res.status_code == 200


@pytest.mark.django_db
class TestGetUpdateUserView:
    """Tests for GetUpdateUserView"""

    def test_user_view_allowed_http_methods(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        get_res = auth_client.get(get_update_user_url)
        assert get_res.status_code == 200

        post_res = auth_client.post(get_update_user_url)
        assert post_res.status_code == 405
        assert post_res.data["detail"] == 'Method \"POST\" not allowed.'

        put_res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert put_res.status_code == 200

        patch_res = auth_client.patch(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert patch_res.status_code == 200

        delete_res = auth_client.delete(get_update_user_url)
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

        options_res = auth_client.options(get_update_user_url)
        assert options_res.status_code == 200
    
    def test_user_view_authentication_is_required(
        self,
        api_client,
        get_update_user_url
    ):
        get_res = api_client.get(get_update_user_url)
        assert get_res.status_code == 403
        assert get_res.data["detail"] == "Authentication credentials were not provided."

    def test_user_view_invalid_access_token(
        self,
        auth_client,
        get_update_user_url,
    ):
        auth_client.credentials(
            HTTP_AUTHORIZATION=
            f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        )
        res = auth_client.get(get_update_user_url)
        assert res.status_code == 403
        assert res.data["detail"] == "Invalid token."

    def test_user_view_successful_user_retrieval(
        self,
        auth_client,
        get_update_user_url
    ):
        res = auth_client.get(get_update_user_url)
        assert res.status_code == 200

    def test_user_retrieval_response_data_fields(
        self,
        auth_client,
        get_update_user_url
    ):
        res = auth_client.get(get_update_user_url)
        assert res.status_code == 200
        assert "id" in res.data
        assert "username" in res.data
        assert "first_name" in res.data
        assert "last_name" in res.data
        assert "email" in res.data
        assert "avatar" in res.data
        assert "bio" in res.data

    def test_user_retrieval_response_data(
        self,
        auth_client,
        expected_user_data,
        get_update_user_url 
    ):
        res = auth_client.get(get_update_user_url)
        assert res.status_code == 200
        assert res.data['username'] == expected_user_data['username']
        assert res.data['first_name'] == expected_user_data['first_name']
        assert res.data['last_name'] == expected_user_data['last_name']
        assert res.data['email'] == expected_user_data['email']
        assert res.data['avatar'] == expected_user_data['avatar']
        assert res.data['bio'] == expected_user_data['bio']

    def test_user_in_response_matches_request_user(
        self,
        auth_client,
        access_token,
        get_update_user_url
    ):
        # Get request user
        token_payload = jwt.decode(
            access_token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id = token_payload['user_id']
        request_user = User.objects.get(id=user_id)

        res = auth_client.get(get_update_user_url)
        assert res.status_code == 200

        # Get response user
        response_user = User.objects.get(id=res.data['id'])

        # Ensure request and response users are the same
        assert request_user.id == response_user.id

    def test_user_update_with_valid_data(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 200
    
    def test_response_user_fields_after_update(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 200

        assert "id" in res.data
        assert "username" in res.data
        assert "first_name" in res.data
        assert "last_name" in res.data
        assert "email" in res.data
        assert "avatar" in res.data
        assert "bio" in res.data
    
    def test_response_user_data_after_update(
        self,
        auth_client,
        update_user_data,
        get_update_user_url,
    ):
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 200

        assert res.data['username'] == update_user_data['username']
        assert res.data['first_name'] == update_user_data['first_name']
        assert res.data['last_name'] == update_user_data['last_name']
        assert res.data['bio'] == update_user_data['bio']

    def test_username_update_fails_if_not_unique(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        second_user = User.objects.create_user(
            username="adelux",
            first_name="Adil",
            last_name="El Bali",
            email="adil.elbali@gmail.com",
            password="adeltest123@"
        )
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["user with this username already exists."]

    def test_email_cannot_be_updated(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data["email"] = "adil.elbali@gmail.com"
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == "Email cannot be updated."

    def test_put_update_user_username_is_required(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data.pop('username')
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["This field is required."]
    
    def test_put_update_user_first_name_is_required(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data.pop('first_name')
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "first_name" in res.data
        assert res.data["first_name"] == ["This field is required."]
    
    def test_put_update_user_last_name_is_required(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data.pop('last_name')
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "last_name" in res.data
        assert res.data["last_name"] == ["This field is required."]

    def test_user_view_accepts_partial_updates_with_patch(
        self,
        auth_client,
        update_user_data,
        get_update_user_url,
        user_instance,
    ):
        update_user_data.pop('username')
        res = auth_client.patch(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )

        assert res.status_code == 200
        assert res.data['username'] == user_instance.username
        assert res.data['first_name'] == update_user_data['first_name']
        assert res.data['last_name'] == update_user_data['last_name']
        assert res.data['bio'] == update_user_data['bio']

    def test_user_update_fails_if_username_is_blank(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data["username"] = ""
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["This field may not be blank."]
    
    def test_user_update_fails_if_first_name_is_blank(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data["first_name"] = ""
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "first_name" in res.data
        assert res.data["first_name"] == ["This field may not be blank."]
    
    def test_user_update_fails_if_last_name_is_blank(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data["last_name"] = ""
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "last_name" in res.data
        assert res.data["last_name"] == ["This field may not be blank."]

    def test_user_update_with_valid_avatar(
        self,
        auth_client,
        update_user_data,
        get_update_user_url,
        setup_cleanup_avatar,
        user_instance
    ):
        assert not user_instance.avatar
        assert user_instance.avatar.name is None

        avatar = setup_cleanup_avatar
        update_user_data["avatar"] = avatar

        # Send the PUT request with the uploaded file
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 200
        assert "avatar" in res.data
        assert res.data["avatar"].endswith(avatar.name)

        user_instance.refresh_from_db()
        assert user_instance.avatar
        assert user_instance.avatar.name is not None

        user_avatar_file_name = str(user_instance.avatar).split('/')[-1]
        assert user_avatar_file_name == avatar.name

    def test_user_update_with_invalid_avatar_file_type(
        self,
        auth_client,
        update_user_data,
        get_update_user_url
    ):
        update_user_data["avatar"] = SimpleUploadedFile(
            "avatar.txt",
            b"not an image",
            content_type="text/plain"
        )
        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )

        assert res.status_code == 400
        assert "avatar" in res.data
        assert res.data["avatar"][0].code == 'invalid_image'

    def test_user_update_with_oversized_avatar(
        self,
        auth_client,
        update_user_data,
        get_update_user_url,
    ):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        oversized_gif = SimpleUploadedFile(
            "oversized.gif",
            small_gif * (2 * 1024 * 1024 + 1),
            content_type="image/gif"
        )

        update_user_data["avatar"] = oversized_gif

        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 400
        assert "avatar" in res.data
        assert res.data["avatar"] == ["Avatar size must be less than 2MB"]

    def test_remove_user_avatar(
        self,
        auth_client,
        update_user_data,
        get_update_user_url,
        setup_cleanup_avatar,
        user_instance
    ):
        # Set valid avatar for user
        avatar = setup_cleanup_avatar
        update_user_data["avatar"] = avatar

        res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert res.status_code == 200
        assert "avatar" in res.data
        assert res.data["avatar"].endswith(avatar.name)

        user_instance.refresh_from_db()
        assert user_instance.avatar
        assert user_instance.avatar.name is not None
        assert user_instance.avatar.name != ""

        # Remove user avatar
        update_user_data["avatar"] = ""

        new_res = auth_client.put(
            get_update_user_url,
            data=update_user_data,
            format='multipart'
        )
        assert new_res.status_code == 200
        assert "avatar" in new_res.data
        assert new_res.data["avatar"] == None

        user_instance.refresh_from_db()
        assert not user_instance.avatar
        assert user_instance.avatar.name == ""
