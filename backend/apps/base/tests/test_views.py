import pytest
from django.urls import reverse
from django.core import mail
from apps.base.models import User


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
def login_credentials(user_instance, user_data):
    return {
        "email": user_data["email"],
        "password": user_data["password"]
    }

@pytest.fixture
def login_url():
    return reverse('login')

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


class TestLoginView:
    """Tests for LoginView"""

    def test_login_view_allowed_http_methods(
        self,
        client,
        login_url,
        login_credentials
    ):
        get_res = client.get(
            login_url,
            content_type="application/json"
        )
        assert get_res.status_code == 405

        post_res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert post_res.status_code == 200

        put_res = client.put(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert put_res.status_code == 405

        delete_res = client.delete(
            login_url,
            content_type="application/json"
        )
        assert delete_res.status_code == 405

        options_res = client.options(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert options_res.status_code == 200

    def test_login_view_unsuccessful_login(
        self,
        client,
        login_url,
        user_instance
    ):
        incorrect_login_data = {
            "email": "elbaliadil@gmail.com",
            "password": "incorrectPassword"
        }
        res = client.post(
            login_url,
            data=incorrect_login_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_email_is_required_in_request_data(
        self,
        client,
        login_url,
        login_credentials
    ):
        login_credentials.pop('email')
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["This field is required."]
    
    def test_login_view_password_is_required_in_request_data(
        self,
        client,
        login_url,
        login_credentials
    ):
        login_credentials.pop('password')
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["This field is required."]

    def test_login_view_email_does_not_exist(
        self,
        client,
        login_url,
        login_credentials
    ):
        login_credentials["email"] = "elbaliadil@gmail.com"
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_incorrect_password(
        self,
        client,
        login_url,
        login_credentials
    ):
        login_credentials["password"] = "incorrectPassword"
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "error" in res.data
        assert res.data["error"][0].startswith("Login Unsuccessful.")

    def test_login_view_successful_login(
        self,
        client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated

    def test_login_view_response_data_after_successful_login(
        self,
        client,
        user_instance,
        login_url,
        login_credentials
    ):
        expected_user_data = {
            "username": "adel",
            "first_name": "Adil",
            "last_name": "El Bali",
            "email": "adxel.elb@gmail.com",
            "avatar": None,
            "bio": None
        }

        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert "access_token" in res.data
        assert "user" in res.data

        user_res_data = res.data['user']
        assert user_res_data['username'] == expected_user_data['username']
        assert user_res_data['first_name'] == expected_user_data['first_name']
        assert user_res_data['last_name'] == expected_user_data['last_name']
        assert user_res_data['email'] == expected_user_data['email']
        assert user_res_data['avatar'] == expected_user_data['avatar']
        assert user_res_data['bio'] == expected_user_data['bio']


    def test_login_view_set_refresh_token_cookie_after_successful_login(
        self,
        client,
        user_instance,
        login_url,
        login_credentials
    ):
        res = client.post(
            login_url,
            data=login_credentials,
            content_type="application/json"
        )
        assert res.status_code == 200
        assert user_instance.is_authenticated
        assert res.cookies.get("refresh_token") is not None


@pytest.mark.django_db
class TestSignUpView:
    """Tests for SignUpView"""

    def test_signup_view_allowed_http_methods(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        get_res = client.get(
            signup_url,
            content_type="application/json"
        )
        assert get_res.status_code == 405

        post_res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert post_res.status_code == 201

        put_res = client.put(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert put_res.status_code == 405

        delete_res = client.delete(
            signup_url,
            content_type="application/json"
        )
        assert delete_res.status_code == 405

        options_res = client.options(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert options_res.status_code == 200

    def test_signup_view_username_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('username')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["This field is required."]
    
    def test_signup_view_first_name_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('first_name')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "first_name" in res.data
        assert res.data["first_name"] == ["This field is required."]

    def test_signup_view_last_name_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('last_name')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "last_name" in res.data
        assert res.data["last_name"] == ["This field is required."]
    
    def test_signup_view_email_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('email')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["This field is required."]
    
    def test_signup_view_password1_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('password1')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password1" in res.data
        assert res.data["password1"] == ["This field is required."]
    
    def test_signup_view_password2_is_required_in_request_data(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        signup_view_data.pop('password2')
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password2" in res.data
        assert res.data["password2"] == ["This field is required."]

    def test_signup_view_username_is_unique(
        self,
        client,
        signup_url,
        signup_view_data,
        user_instance
    ):
        signup_view_data['username'] = 'adel'
        signup_view_data['email'] = 'adxel.elbali@gmail.com'
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "username" in res.data
        assert res.data["username"] == ["user with this username already exists."]
    
    def test_signup_view_email_is_unique(
        self,
        client,
        signup_url,
        signup_view_data,
        user_instance
    ):
        signup_view_data['username'] = 'adxel'
        signup_view_data['email'] = 'adxel.elb@gmail.com'
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["user with this email already exists."]
    
    def test_signup_view_invalid_email(
        self,
        client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data['email'] = 'adel.com'
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "email" in res.data
        assert res.data["email"] == ["Enter a valid email address."]

    def test_signup_view_mismatched_passwords(
        self,
        client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "adeltest123"
        signup_view_data["password2"] = "deltest123"
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["The two password fields do not match."]
    
    def test_signup_view_invalid_short_password(
        self,
        client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "128abc"
        signup_view_data["password2"] = "128abc"
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert (
            res.data["password"] ==
            ["This password is too short. It must contain at least 8 characters."]
        )

    def test_signup_view_invalid_numeric_password(
        self,
        client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "14958373"
        signup_view_data["password2"] = "14958373"
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["This password is entirely numeric."]

    def test_signup_view_invalid_similar_to_user_attribute_password(
        self,
        client,
        signup_url,
        signup_view_data,
    ):
        signup_view_data["password1"] = "elbali12"
        signup_view_data["password2"] = "elbali12"
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "password" in res.data
        assert res.data["password"] == ["The password is too similar to the last name."]
    
    def test_signup_view_successful_signup(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 201

    def test_signup_view_response_data_after_successful_signup(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        expected_user_data = {
            "username": "adel",
            "first_name": "Adil",
            "last_name": "El Bali",
            "email": "adxel.elb@gmail.com",
            "avatar": None,
            "bio": None
        }

        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 201
        assert "access_token" in res.data
        assert "user" in res.data

        user = User.objects.get(id=res.data['user']['id'])
        assert user.is_authenticated

        user_res_data = res.data['user']
        assert user_res_data['username'] == expected_user_data['username']
        assert user_res_data['first_name'] == expected_user_data['first_name']
        assert user_res_data['last_name'] == expected_user_data['last_name']
        assert user_res_data['email'] == expected_user_data['email']
        assert user_res_data['avatar'] == expected_user_data['avatar']
        assert user_res_data['bio'] == expected_user_data['bio']

    def test_signup_view_set_refresh_token_cookie_after_successful_signup(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 201
        assert res.cookies.get("refresh_token") is not None

        user = User.objects.get(id=res.data['user']['id'])
        assert user.is_authenticated

    def test_signup_view_confirmation_email_after_successful_signup(
        self,
        client,
        signup_url,
        signup_view_data
    ):
        res = client.post(
            signup_url,
            data=signup_view_data,
            content_type="application/json"
        )
        assert res.status_code == 201
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.from_email == "elbadil.testing@gmail.com"
        assert email.to == ['adxel.elb@gmail.com']
        assert email.subject == "Welcome to Stocker"
        assert email.body == "You have Successfully Created A Stocker Account."

