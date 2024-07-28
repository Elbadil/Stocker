from rest_framework.serializers import ModelSerializer
from ..models import Item


class ItemSerializer(ModelSerializer):
    """Product Model Serializer"""
    class Meta:
        model = Item
        fields = '__all__'
