from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
from .models import User


class TokenVersionAuthentication(BaseAuthentication):
    """Validates the version of the jwt sent with authenticated requests"""
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['user_id']
            token_version = payload['token_version']
            user = User.objects.get(id=user_id)
            if user.token_version != token_version:
                raise AuthenticationFailed('Invalid or expired token.')
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired.')
        except (User.DoesNotExist, jwt.InvalidTokenError):
            raise AuthenticationFailed('Invalid token.')
        except Exception as e:
            # Log exception details if necessary
            raise AuthenticationFailed('Authentication failed due to an unexpected error.')
