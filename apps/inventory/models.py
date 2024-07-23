from django.db import models
from apps.base.models import User
from utils.models import BaseModel


class Category(BaseModel):
    """Product Category Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, blank=False)

    def __str__(self) -> str:
        return f'Category: -{self.name}- Added by -{self.user.username}-'


class Supplier(BaseModel):
    """Product Supplier Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        return f'Supplier: -{self.name}- Added by -{self.user.username}-'


class AddAttr(BaseModel):
    """Product's Additional Attributes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)

    class Meta:
        db_table = 'inventory_add_attr'

    def __str__(self) -> str:
        return self.name


class Post(BaseModel):
    """Product's Post"""
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    """Product Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=300, blank=False)
    quantity = models.IntegerField(blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=False)
    picture = models.ImageField(null=True, upload_to='inventory/images/', blank=True)
    other_attr = models.ManyToManyField(AddAttr, related_name='other_attr', blank=True)
    posts = models.ManyToManyField(Post, related_name='posts', blank=True)

    def total_price(self):
        """Returns Quantity times Price"""
        return self.quantity * self.price

    def __str__(self) -> str:
        return f'{self.name} added by - {self.user.username} -'


class AddAttrDescription(BaseModel):
    """Product's Additional Attributes Description"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    add_attr = models.ForeignKey(AddAttr, on_delete=models.CASCADE, null=True)
    body = models.CharField(max_length=300)

    class Meta:
        db_table = 'inventory_add_attr_description'

    def __str__(self) -> str:
        return f'{self.product.name} added by - {self.product.user.username} - is available on {self.add_attr.name}: {self.body}'
