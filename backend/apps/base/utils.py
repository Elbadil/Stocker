from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


def get_tokens_for_user(user: User):
    """Adds more user data to the access jwt"""
    refresh = RefreshToken.for_user(user)
    refresh.payload['token_version'] = user.token_version

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }
