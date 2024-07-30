from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.sessions.models import Session
from .serializers import ItemSerializer
from ...base.models import User
from ..models import Item
from .utils import request_validation_errors


@api_view(['GET'])
def userItems(request, user_id):
    """Returns a list of user item's objects"""
    validation_response = request_validation_errors(request, user_id)
    if validation_response:
        return validation_response 
    user_items = Item.objects.filter(user__id=user_id)
    serializer = ItemSerializer(user_items, many=True)
    return Response(serializer.data)
