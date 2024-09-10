from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer


def get_tokens_for_user(request, user: User):
    """Adds more user data to the access jwt"""
    refresh = RefreshToken.for_user(user)
    user_data = UserSerializer(user, context={'request': request}).data
    user_data.pop('bio');
    refresh.payload.update(user_data)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }
