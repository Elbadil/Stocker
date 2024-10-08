from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from .models import User


def get_tokens_for_user(user: User) -> dict:
    """Adds more user data to the access jwt"""
    refresh = RefreshToken.for_user(user)
    refresh.payload['token_version'] = user.token_version

    return {
        'refresh': str(refresh),
        'refresh_payload': refresh.payload,
        'access': str(refresh.access_token)
    }


def set_refresh_token(response, token: str, token_payload: dict) -> None:
    """Sets a refresh token as an HTTP-only cookie in the response"""
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite='Lax',
        expires=token_payload['exp'],
        max_age=token_payload['exp'] - datetime.now().timestamp(),
    )
