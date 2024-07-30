from rest_framework import serializers
from ..models import Item


class ItemSerializer(serializers.ModelSerializer):
    """Product Model Serializer"""
    # read_only=True ensures that the category field cannot be modified
    # during item create or update operations, making it clear that we're
    # setting category.name to category only for display purposes
    category = serializers.CharField(source='category.name', read_only=True)
    supplier = serializers.CharField(source='supplier.name', read_only=True)
    created_at = serializers.DateTimeField(format='%m/%d/%Y', read_only=True)
    updated_at = serializers.DateTimeField(format='%m/%d/%Y', read_only=True)
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'quantity',
            'price',
            'variants',
            'total_price',
            'category',
            'supplier',
            'picture',
            'created_at',
            'updated',
            'updated_at',
            'user'
        ]

    def get_total_price(self, item):
        total_price = item.price * item.quantity
        return float(total_price)

    def get_price(self, item):
        return float(item.price)

    def get_variants(self, item):
        variants = []
        for variant in item.variants.all():
            variant_obj = {'name': variant.name}
            variant_obj['options'] = [option.body
                                     for option in variant.variantoptions_set.all()
                                     if option.item == item]
            variants.append(variant_obj)
        return variants if len(variants) > 0 else None
