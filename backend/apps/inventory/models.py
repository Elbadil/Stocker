from django.db import models
from apps.base.models import User
from utils.models import BaseModel
from ..client_orders.models import ClientOrderedItem


class Category(BaseModel):
    """Item's Category Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, blank=False)

    def __str__(self) -> str:
        if self.user:
            return f'Category: -{self.name}- Added by -{self.user.username}-'
        return self.name


class Supplier(BaseModel):
    """Item's Supplier Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        if self.user:
            return f'Supplier: -{self.name}- Added by -{self.user.username}-'
        return self.name


class Variant(BaseModel):
    """Item's Variants"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)

    class Meta:
        db_table = 'inventory_variant'

    def __str__(self) -> str:
        if self.user:
            return f'Variant: -{self.name}- Added by -{self.user.username}-'
        return self.name


def item_picture_path(item, filename):
    return f"inventory/images/{item.user.id}/{filename}"

class Item(BaseModel):
    """Item Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=300, blank=False)
    quantity = models.IntegerField(blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=False)
    picture = models.ImageField(null=True, upload_to=item_picture_path, blank=True)
    variants = models.ManyToManyField(Variant, related_name='variants', blank=True)
    updated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_price(self):
        """Returns Quantity times Price"""
        return self.quantity * self.price
    
    @property
    def total_orders(self):
        return ClientOrderedItem.objects.filter(item__id=self.id).count()

    def __str__(self) -> str:
        if self.user:
            return f'{self.name} added by - {self.user.username} -'
        return self.name


class VariantOption(BaseModel):
    """Item's Variant Description"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True)
    body = models.CharField(max_length=300)

    class Meta:
        db_table = 'inventory_variant_option'

    def __str__(self) -> str:
        return f'{self.item.name} added by - {self.item.user.username} - is available on {self.variant.name}: {self.body}'
