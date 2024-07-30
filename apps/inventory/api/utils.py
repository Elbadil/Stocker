from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpRequest
from typing import Union
from ...base.models import User


def request_validation_errors(request: HttpRequest, user_id: str) -> Union[JsonResponse, None]:
    """Validates the request by checking if the request user is
    authenticated, exists, and matches the given user_id"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'unauthenticated'}, status=401)

    try:
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValidationError):
        return JsonResponse({'error': 'user not found'}, status=404)

    if request.user != user:
        return JsonResponse({'error': 'unauthorized'}, status=401)

    return None
