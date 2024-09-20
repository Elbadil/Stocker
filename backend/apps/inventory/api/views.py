from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ItemSerializer
from ...base.models import User
from ..models import Item, Category
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


@api_view(['GET'])
def categoryItems(request, category_id):
    """Returns a list of user item's objects for a specified category"""
    user = request.user
    validation_response = request_validation_errors(request, user.id)
    if validation_response:
        return validation_response 
    category_items = Item.objects.filter(user=user, category__id=category_id)
    serializer = ItemSerializer(category_items, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def supplierItems(request, supplier_id):
    """Returns a list of user item's objects for a specified category"""
    user = request.user
    validation_response = request_validation_errors(request, user.id)
    if validation_response:
        return validation_response 
    supplier_id_items = Item.objects.filter(user=user, supplier__id=supplier_id)
    serializer = ItemSerializer(supplier_id_items, many=True)
    return Response(serializer.data)
