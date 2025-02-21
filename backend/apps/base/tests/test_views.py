import pytest
import os
import jwt
import shutil
from urllib.parse import urlparse, parse_qs
from dateutil import parser
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.urls import reverse
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from datetime import datetime, timezone, timedelta
from apps.base.models import User, Activity
from apps.base.factories import ActivityFactory


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
def change_password_data():
    return {
        "old_password": "adeltest123@",
        "new_password1": "adlux567@",
        "new_password2": "adlux567@"
    }

@pytest.fixture
def reset_password_data(change_password_data):
    return {
        "new_password1": change_password_data["new_password1"],
        "new_password2": change_password_data["new_password2"]
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

@pytest.fixture
def change_password_url():
    return reverse('change_password')

@pytest.fixture
def request_pwd_reset_url():
    return reverse('request_password_reset')

@pytest.fixture
def valid_reset_password_url(user_instance):
    uidb64 = urlsafe_base64_encode(force_bytes(user_instance.id))
    token = PasswordResetTokenGenerator().make_token(user_instance)
    return reverse(
        'password_reset',
        kwargs={
            'uidb64': uidb64,
            'token': token
        }
    )

@pytest.fixture
def user_activities_url():
    return reverse('get_user_activities')


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


@pytest.mark.django_db
class TestChangePasswordView:
    """Tests for the ChangePasswordView"""

    def test_change_pwd_view_allowed_http_methods(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        get_res = auth_client.get(change_password_url)
        assert get_res.status_code == 405
        assert get_res.data["detail"] == 'Method \"GET\" not allowed.'

        put_res = auth_client.put(change_password_url)
        assert put_res.status_code == 405
        assert put_res.data["detail"] == 'Method \"PUT\" not allowed.'

        delete_res = auth_client.delete(change_password_url)
        assert delete_res.status_code == 405
        assert delete_res.data["detail"] == 'Method \"DELETE\" not allowed.'

        post_res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert post_res.status_code == 200

    def test_change_pwd_view_authentication_is_required(
        self,
        api_client,
        change_password_data,
        change_password_url
    ):
        res = api_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."
    
    def test_change_pwd_view_new_old_password_is_required(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data.pop('old_password')
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "old_password" in res.data
        assert res.data["old_password"] == ["This field is required."]

    def test_change_pwd_view_new_password1_is_required(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data.pop('new_password1')
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password1" in res.data
        assert res.data["new_password1"] == ["This field is required."]
    
    def test_change_pwd_view_new_password2_is_required(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data.pop('new_password2')
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password2" in res.data
        assert res.data["new_password2"] == ["This field is required."]

    def test_change_pwd_view_with_invalid_old_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["old_password"] = "invalidOldPassword"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "old_password" in res.data
        assert res.data["old_password"] == ["Old password is incorrect."]
    
    def test_new_password_is_similar_to_the_old_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "adeltest123@"
        change_password_data["new_password2"] = "adeltest123@"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["New password cannot be the same as the old password."]
        )

    def test_change_pwd_view_with_mismatched_new_passwords(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "adlux567@"
        change_password_data["new_password2"] = "adlux57@@"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["The two new password fields do not match."]
        )
    
    def test_change_pwd_view_with_invalid_new_short_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "128abc"
        change_password_data["new_password2"] = "128abc"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_change_pwd_view_with_invalid_numeric_new_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "14958373"
        change_password_data["new_password2"] = "14958373"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["This password is entirely numeric."]
        )

    def test_change_pwd_view_with_invalid_common_new_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "abc12345"
        change_password_data["new_password2"] = "abc12345"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert res.data["new_password"] == ["This password is too common."]

    def test_invalid_similar_to_user_attribute_new_password(
        self,
        auth_client,
        change_password_data,
        change_password_url
    ):
        change_password_data["new_password1"] = "elbali12"
        change_password_data["new_password2"] = "elbali12"
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["The password is too similar to the last name."]
        )

    def test_increment_user_token_version_after_pwd_change(
        self,
        auth_client,
        change_password_data,
        change_password_url,
        user_instance
    ):
        assert user_instance.token_version == 1

        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200
        
        user_instance.refresh_from_db()
        assert user_instance.token_version == 2

    def test_access_token_in_response_after_pwd_change(
        self,
        auth_client,
        change_password_data,
        change_password_url,
    ):
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200
        assert "access_token" in res.data
    
    def test_valid_access_token_in_response_after_pwd_change(
        self,
        auth_client,
        change_password_data,
        change_password_url,
    ):
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200
        assert "access_token" in res.data

        access_token = res.data["access_token"]
        verify_token_url = reverse('token_verify')
        verify_res = auth_client.post(
            verify_token_url,
            data={'token': access_token}
        )

        assert verify_res.status_code == 200

    def test_new_access_token_in_response_after_pwd_change(
        self,
        auth_client,
        access_token,
        change_password_data,
        change_password_url,
    ):
        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200
        assert "access_token" in res.data

        new_access_token = res.data["access_token"]
        assert new_access_token != access_token

    def test_new_refresh_token_is_set_in_cookies_after_pwd_change(
        self,
        auth_client,
        change_password_data,
        change_password_url,
    ):
        refresh_token = auth_client.cookies.get('refresh_token')

        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200

        new_refresh_token = res.cookies.get("refresh_token")
        assert new_refresh_token is not None
        assert new_refresh_token.value != refresh_token.value
    
    def test_new_refresh_token_version_matches_user_new_token_version(
        self,
        auth_client,
        change_password_data,
        change_password_url,
        user_instance
    ):
        refresh_token = auth_client.cookies.get('refresh_token')
        token_payload = jwt.decode(
            refresh_token.value, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        assert token_payload["token_version"] == 1
        assert user_instance.token_version == 1

        res = auth_client.post(
            change_password_url,
            data=change_password_data,
            format='json'
        )
        assert res.status_code == 200

        new_refresh_token = res.cookies.get("refresh_token")
        assert new_refresh_token is not None

        new_token_payload = jwt.decode(
            new_refresh_token.value, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_instance.refresh_from_db()
        assert new_token_payload["token_version"] == 2
        assert user_instance.token_version == 2
        assert (
            new_token_payload["token_version"] ==
            user_instance.token_version
        )


@pytest.mark.django_db
class TestRequestPasswordResetView:
    """"Tests for the RequestPasswordResetView"""

    def test_req_pwd_reset_allowed_http_methods(
        self,
        api_client,
        user_instance,
        request_pwd_reset_url
    ):
        get_res = api_client.get(request_pwd_reset_url)
        assert get_res.status_code == 405

        post_res = api_client.post(
            request_pwd_reset_url,
            data={"email": user_instance.email},
            format="json"
        )
        assert post_res.status_code == 200

        put_res = api_client.put(request_pwd_reset_url)
        assert put_res.status_code == 405

        delete_res = api_client.delete(request_pwd_reset_url)
        assert delete_res.status_code == 405

    def test_req_pwd_reset_email_is_required(
        self,
        api_client,
        request_pwd_reset_url
    ):
        res = api_client.post(request_pwd_reset_url)

        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == "Email is required."
    
    def test_req_pwd_reset_with_valid_email(
        self,
        api_client,
        user_instance,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": user_instance.email},
            format="json"
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert (
            res.data["message"] == 
            "If the email is associated with an account, a reset link has been sent."
        )

    def test_req_pwd_reset_with_invalid_email(
        self,
        api_client,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": "adel.com"},
            format="json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == "Enter a valid email address."

    def test_req_pwd_reset_with_invalid_inexistent_email(
        self,
        api_client,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": "adelu@gmail.com"},
            format="json"
        )
        assert res.status_code == 200
        assert "message" in res.data
        assert (
            res.data["message"] == 
            "If the email is associated with an account, a reset link has been sent."
        )

    def test_email_received_after_reset_pwd_req(
        self,
        api_client,
        user_instance,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": user_instance.email},
            format="json"
        )
        assert res.status_code == 200
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.from_email == "elbadil.testing@gmail.com"
        assert email.to == ['adxel.elb@gmail.com']
        assert email.subject == "Stocker Password Reset"
        assert email.body.startswith("You can reset your password here:")

    def test_no_email_is_sent_if_the_provided_email_does_not_exist(
        self,
        api_client,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": "adelu@gmail.com"},
            format="json"
        )

        assert res.status_code == 200
        assert len(mail.outbox) == 0

    def test_user_id_is_encoded_in_b64_in_reset_url(
        self,
        api_client,
        user_instance,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": user_instance.email},
            format="json"
        )
        assert res.status_code == 200
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        reset_url = email.body.split(': ')[1]
        parsed_reset_url = urlparse(reset_url)
        assert parsed_reset_url.path.startswith("/auth/password-reset/")

        path_segments = parsed_reset_url.path.split('/')
        assert len(path_segments) > 3

        user_uidb64 = path_segments[3]
        user_uidb64_decoded = force_str(urlsafe_base64_decode(user_uidb64))
        assert user_instance.id == user_uidb64_decoded

    def test_valid_reset_token_for_user_in_pwd_reset_url(
        self,
        api_client,
        user_instance,
        request_pwd_reset_url
    ):
        res = api_client.post(
            request_pwd_reset_url,
            data={"email": user_instance.email},
            format="json"
        )
        assert res.status_code == 200
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        reset_url = email.body.split(': ')[1]
        parsed_reset_url = urlparse(reset_url)
        assert parsed_reset_url.path.startswith("/auth/password-reset/")

        path_segments = parsed_reset_url.path.split('/')
        assert len(path_segments) > 4

        reset_pwd_token = path_segments[4]
        assert (
            PasswordResetTokenGenerator()
            .check_token(user_instance, reset_pwd_token)
        )


@pytest.mark.django_db
class TestResetPasswordView:
    """Tests for the ResetPasswordView"""

    def test_reset_password_allowed_http_methods(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        get_res = api_client.get(valid_reset_password_url)
        assert get_res.status_code == 405

        put_res = api_client.put(valid_reset_password_url)
        assert put_res.status_code == 405

        delete_res = api_client.delete(valid_reset_password_url)
        assert delete_res.status_code == 405

        post_res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert post_res.status_code == 200

    def test_reset_password_with_valid_data(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 200
        assert res.data["message"] == "User password has been successfully reset."

    def test_new_password_after_password_reset(
        self,
        api_client,
        user_instance,
        reset_password_data,
        valid_reset_password_url
    ):
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 200
        assert res.data["message"] == "User password has been successfully reset."

        user_instance.refresh_from_db()
        assert user_instance.check_password(reset_password_data["new_password1"])

    def test_uidb64_in_reset_url_is_users_id_encoded_in_b64(
        self,
        user_instance,
        valid_reset_password_url,
    ):
        url_paths = valid_reset_password_url.split('/')
        assert len(url_paths) > 4

        uidb64 = url_paths[4]
        uidb64_decoded = force_str(urlsafe_base64_decode(uidb64))
        assert user_instance.id == uidb64_decoded

    def test_invalid_uidb64_for_user_in_reset_url(
        self,
        api_client,
        user_instance,
        reset_password_data,
    ):
        uidb64 = 'InvalidUidb64'
        token = PasswordResetTokenGenerator().make_token(user_instance)
        url = reverse(
            'password_reset',
            kwargs={
                "uidb64": uidb64,
                "token": token
            }
        )
        res = api_client.post(
            url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "Something went wrong. Please request a new password reset."

    def test_valid_reset_token_for_user_in_reset_url(
        self,
        user_instance,
        valid_reset_password_url,
    ):
        url_paths = valid_reset_password_url.split('/')
        assert len(url_paths) > 5

        token = url_paths[5]
        assert PasswordResetTokenGenerator().check_token(user_instance, token)
    
    def test_invalid_reset_token_for_user_in_reset_url(
        self,
        api_client,
        user_instance,
        reset_password_data,
    ):
        uidb64 = urlsafe_base64_encode(force_bytes(user_instance.id))
        token = 'InvalidResetToken'
        url = reverse(
            'password_reset',
            kwargs={
                "uidb64": uidb64,
                "token": token
            }
        )
        res = api_client.post(
            url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"] == "Something went wrong. Please request a new password reset."

    def test_increment_user_token_version_after_password_reset(
        self,
        api_client,
        user_instance,
        reset_password_data,
        valid_reset_password_url
    ):
        assert user_instance.token_version == 1

        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 200

        user_instance.refresh_from_db()
        assert user_instance.token_version == 2

    def test_reset_password_new_password1_is_required(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data.pop('new_password1')
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password1" in res.data
        assert res.data["new_password1"] == ["This field is required."]

    def test_reset_password_new_password2_is_required(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data.pop('new_password2')
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password2" in res.data
        assert res.data["new_password2"] == ["This field is required."]

    def test_reset_password_mismatched_new_passwords(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data["new_password1"] = "adlux567@"
        reset_password_data["new_password2"] = "adlux57@@"
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["The two new password fields do not match."]
        )

    def test_reset_password_invalid_short_password(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data["new_password1"] = "128abc"
        reset_password_data["new_password2"] = "128abc"
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )
    
    def test_reset_password_invalid_numeric_new_password(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data["new_password1"] = "14958373"
        reset_password_data["new_password2"] = "14958373"
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["This password is entirely numeric."]
        )

    def test_reset_password_invalid_common_new_password(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data["new_password1"] = "abc12345"
        reset_password_data["new_password2"] = "abc12345"
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert res.data["new_password"] == ["This password is too common."]
    
    def test_invalid_similar_to_user_attribute_new_password(
        self,
        api_client,
        reset_password_data,
        valid_reset_password_url
    ):
        reset_password_data["new_password1"] = "elbali12"
        reset_password_data["new_password2"] = "elbali12"
        res = api_client.post(
            valid_reset_password_url,
            data=reset_password_data,
            format="json"
        )
        assert res.status_code == 400
        assert "new_password" in res.data
        assert (
            res.data["new_password"] ==
            ["The password is too similar to the last name."]
        )


@pytest.mark.django_db
class TestGetUserActivitiesView:
    """Test for GetUserActivities View"""

    def test_get_user_activities_allowed_http_methods(
        self,
        auth_client,
        user_activities_url,
    ):
        get_res = auth_client.get(user_activities_url)
        assert get_res.status_code == 200

        put_res = auth_client.put(user_activities_url)
        assert put_res.status_code == 405

        delete_res = auth_client.delete(user_activities_url)
        assert delete_res.status_code == 405

        post_res = auth_client.post(user_activities_url)
        assert post_res.status_code == 405

    def test_get_user_activities_authentication_is_required(
        self,
        api_client,
        user_activities_url,
    ):
        res = api_client.get(user_activities_url)

        assert res.status_code == 403
        assert res.data["detail"] == "Authentication credentials were not provided."

    def test_get_user_activities_with_valid_auth_credentials(
        self,
        auth_client,
        user_activities_url,
    ):
        get_res = auth_client.get(user_activities_url)
        assert get_res.status_code == 200

    def test_get_user_activities_response_fields(
        self,
        auth_client,
        user_instance,
        user_activities_url,
    ):
        ActivityFactory.create_batch(4, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "next" in res.data
        assert "previous" in res.data
        assert "results" in res.data
        assert isinstance(res.data["results"], list)

    def test_user_activities_are_in_the_results_field_of_the_response(
        self,
        auth_client,
        user_instance,
        user_activities_url,
    ):
        activities = ActivityFactory.create_batch(4, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(activities) == len(res.data["results"])

    def test_user_activities_fields_in_results(
        self,
        auth_client,
        user_instance,
        user_activities_url,
    ):
        activities = ActivityFactory.create_batch(4, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert isinstance(res.data["results"], list)
        assert len(activities) == len(res.data["results"])

        first_activity = res.data["results"][0]
        assert type(first_activity) == dict
        assert "id" in first_activity

        assert "user" in first_activity
        user = first_activity["user"]
        assert "username" in user
        assert "avatar" in user

        assert "action" in first_activity
        assert "model_name" in first_activity
        assert "object_ref" in first_activity
        assert "created_at" in first_activity

    def test_user_activities_field_types_in_results(
        self,
        auth_client,
        user_instance,
        user_activities_url,
    ):
        activities = ActivityFactory.create_batch(4, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert isinstance(res.data["results"], list)
        assert len(activities) == len(res.data["results"])

        first_activity = res.data["results"][0]
        assert type(first_activity) == dict
        assert type(first_activity["id"]) == str

        assert type(first_activity["user"]) == dict
        user = first_activity["user"]
        assert type(user["username"]) == str
        assert isinstance(user["avatar"], (str, type(None)))

        assert type(first_activity["action"]) == str
        assert type(first_activity["model_name"]) == str
        assert type(first_activity["object_ref"]) == list
        assert type(first_activity["created_at"]) == str

    def test_get_user_activities_returns_request_user_activities(
        self,
        api_client,
        user_instance,
        access_token,
        user_activities_url,
    ):
        ActivityFactory.create_batch(4, user=user_instance)
        token_payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = token_payload["user_id"]
        req_user = User.objects.get(id=user_id)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        res = api_client.get(user_activities_url)
        assert res.status_code == 200
        assert "results" in res.data

        first_activity = res.data["results"][0]
        assert "user" in first_activity
        user = first_activity["user"]
        assert "username" in user

        res_user = User.objects.get(username=user["username"])
        assert res_user.id == req_user.id

    def test_get_user_activities_with_zero_activities(
        self,
        auth_client,
        user_instance,
        user_activities_url
    ):
        ActivityFactory.create_batch(0, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert isinstance(res.data["results"], list)
        assert len(res.data["results"]) == 0

    def test_maximum_ten_activities_per_request(
        self,
        auth_client,
        user_instance,
        user_activities_url
    ):
        activities = ActivityFactory.create_batch(20, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "next" in res.data
        assert res.data["next"] is not None

        assert "previous" in res.data
        assert res.data["previous"] is None

        assert "results" in res.data
        assert len(activities) != len(res.data["results"])
        assert len(res.data["results"]) == 10
    
    def test_get_user_activities_uses_cursor_method_for_pagination(
        self,
        auth_client,
        user_instance,
        user_activities_url
    ):
        ActivityFactory.create_batch(20, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(res.data["results"]) == 10

        assert "next" in res.data
        assert res.data["next"] is not None
        next_page_url = res.data["next"]
        assert "cursor" in next_page_url

        query_params = parse_qs(urlparse(next_page_url).query)
        assert "cursor" in query_params

    def test_next_field_in_response_data(
        self,
        auth_client,
        user_instance,
        user_activities_url    
    ):
        ActivityFactory.create_batch(20, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(res.data["results"]) == 10

        assert "next" in res.data
        next_page = res.data["next"]
        assert next_page is not None

        # Validate next is a URL
        assert next_page.startswith("http")

        # Ensure it contains query parameters for pagination
        query_params = parse_qs(urlparse(next_page).query)
        assert query_params

        # Validate that 'cursor' is in the query params
        assert "cursor" in query_params

        # Ensure it belongs to the same endpoint
        assert user_activities_url in next_page

        # Send request to get next page
        next_res = auth_client.get(next_page)

        assert next_res.status_code == 200
        assert "results" in next_res.data
        assert len(next_res.data["results"]) == 10

    def test_get_next_page_of_activities_if_more_than_ten(
        self,
        auth_client,
        user_instance,
        user_activities_url
    ):
        # Create 20 activity entries
        ActivityFactory.create_batch(20, user=user_instance)

        # Get first 10 activities
        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "previous" in res.data
        assert res.data["previous"] is None
        assert "results" in res.data
        assert len(res.data["results"]) == 10

        assert "next" in res.data
        assert res.data["next"] is not None
        next_page_url = res.data["next"]

        # Get second 10 activities using next page url
        next_page_res = auth_client.get(next_page_url)

        assert next_page_res.status_code == 200
        assert "previous" in next_page_res.data
        assert next_page_res.data["previous"] is not None

        assert "results" in next_page_res.data
        assert len(next_page_res.data["results"]) == 10

    def test_previous_field_in_response_data(
        self,
        auth_client,
        user_instance,
        user_activities_url    
    ):
        ActivityFactory.create_batch(20, user=user_instance)

        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(res.data["results"]) == 10

        assert "previous" in res.data
        assert res.data["previous"] is None

        assert "next" in res.data
        next_page = res.data["next"]
        assert next_page is not None

        # Send request to get next page
        next_res = auth_client.get(next_page)

        assert next_res.status_code == 200
        assert "results" in next_res.data
        assert len(next_res.data["results"]) == 10

        assert "previous" in next_res.data
        assert next_res.data["previous"] is not None
        previous_page = next_res.data["previous"]

        # Validate previous is a URL
        assert previous_page.startswith("http")

        # Ensure it contains query parameters for pagination
        query_params = parse_qs(urlparse(previous_page).query)
        assert query_params

        # Validate that 'cursor' is in the query params
        assert "cursor" in query_params

        # Ensure it belongs to the same endpoint
        assert user_activities_url in previous_page

        # Send request to get previous page
        previous_res = auth_client.get(next_page)

        assert previous_res.status_code == 200
        assert "results" in previous_res.data
        assert len(previous_res.data["results"]) == 10

    def test_get_previous_activities_page(
        self,
        auth_client,
        user_instance,
        user_activities_url
    ):
        # Create 20 activity entries
        ActivityFactory.create_batch(20, user=user_instance)

        # Get first 10 activities
        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "previous" in res.data
        assert res.data["previous"] is None
        assert "results" in res.data
        assert len(res.data["results"]) == 10

        assert "next" in res.data
        assert res.data["next"] is not None
        next_page_url = res.data["next"]

        # Get second 10 activities using next page url
        next_res = auth_client.get(next_page_url)

        assert next_res.status_code == 200
        assert "results" in next_res.data
        assert len(next_res.data["results"]) == 10

        assert "previous" in next_res.data
        assert next_res.data["previous"] is not None
        prev_page_url = next_res.data["previous"]

        # Get first 10 activities again using previous page url
        prev_res = auth_client.get(prev_page_url)

        assert prev_res.status_code == 200
        assert "results" in prev_res.data
        assert len(prev_res.data["results"]) == 10

    def test_activities_sorted_desc_by_created_at(
        self,
        auth_client,
        user_instance,
        user_activities_url   
    ):
        # Create 20 activity entries
        activities = ActivityFactory.create_batch(20, user=user_instance)

        # Assign unique timestamps manually
        now = datetime.now(timezone.utc)
        for i, activity in enumerate(activities):
            activity.created_at = now + timedelta(seconds=i)

        # Perform bulk update to save changes
        Activity.objects.bulk_update(activities, ['created_at'])

        # Get first 10 activities
        res = auth_client.get(user_activities_url)

        assert res.status_code == 200
        assert "results" in res.data
        assert len(res.data["results"]) == 10
        first_page_activities = res.data["results"]

        first_page_activities_sorted = sorted(
            first_page_activities,
            key=lambda x: parser.parse(x['created_at']), reverse=True
        )

        assert first_page_activities == first_page_activities_sorted

        assert "previous" in res.data
        assert res.data["previous"] is None

        assert "next" in res.data
        next_page = res.data["next"]
        assert next_page is not None

        # Get second 10 activities using next page url
        next_res = auth_client.get(next_page)

        assert next_res.status_code == 200
        assert "previous" in next_res.data
        assert next_res.data["previous"] is not None

        assert "results" in next_res.data
        assert len(next_res.data["results"]) == 10

        second_page_activities = next_res.data["results"]
        assert (
            parser.parse(first_page_activities[-1]['created_at']) > 
            parser.parse(second_page_activities[0]['created_at'])
        )
