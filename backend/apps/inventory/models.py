from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.base.models import User
from utils.models import BaseModel
from apps.client_orders.models import ClientOrderedItem
from apps.supplier_orders.models import Supplier, SupplierOrderedItem


class Category(BaseModel):
    """Item's Category Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, blank=False)

    def __str__(self) -> str:
        if self.created_by:
            return f'Category: -{self.name}- Added by -{self.created_by.username}-'
        return self.name


class Variant(BaseModel):
    """Item's Variants"""
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200)

    class Meta:
        db_table = 'inventory_variant'

    def __str__(self) -> str:
        if self.created_by:
            return f'Variant: -{self.name}- Added by -{self.created_by.username}-'
        return self.name


def item_picture_path(item, filename):
    return f"inventory/images/{item.created_by.id}/{filename}"

class Item(BaseModel):
    """Item Model"""
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(
        Category,
        related_name="items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    name = models.CharField(max_length=300, blank=False)
    quantity = models.IntegerField(validators=[MinValueValidator(0)], blank=False)
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))],
        blank=False
    )
    picture = models.ImageField(null=True, upload_to=item_picture_path, blank=True)
    variants = models.ManyToManyField(Variant, related_name='items', blank=True)
    in_inventory = models.BooleanField(default=False)
    updated = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_price(self):
        """Returns Quantity times Price"""
        return self.quantity * self.price
    
    @property
    def total_client_orders(self):
        return ClientOrderedItem.objects.filter(item__id=self.id).count()

    @property
    def total_supplier_orders(self):
        return SupplierOrderedItem.objects.filter(item__id=self.id).count()

    def __str__(self) -> str:
        if self.created_by:
            return f'{self.name} by -{self.created_by.username}-'
        return self.name


class VariantOption(BaseModel):
    """Item's Variant Description"""
    item = models.ForeignKey(
        Item,
        related_name="variant_options",
        on_delete=models.CASCADE,
        null=True
    )
    variant = models.ForeignKey(
        Variant,
        related_name="options",
        on_delete=models.CASCADE,
        null=True
    )
    body = models.CharField(max_length=300)

    class Meta:
        db_table = 'inventory_variant_option'

    def __str__(self) -> str:
        return (
            f'{self.item.name} added by -'
            f'{self.item.created_by.username}- is available on '
            f'{self.variant.name}: {self.body}'
        )
