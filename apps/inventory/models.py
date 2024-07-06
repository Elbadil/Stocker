from django.db import models
from apps.base.models import User
from utils.models import BaseModel


class Category(BaseModel, models.Model):
    """Product Category Model"""
    name = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name


class Supplier(BaseModel, models.Model):
    """Product Supplier Model"""
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name


# class AdditionalAttr(BaseModel, models.Model):
#     """Product's Additional Attributes"""
#     name = models.CharField(max_length=200)
#     description = models.CharField(max_length=300)

#     class Meta:
#         db_table = 'additional_attr'

#     def __str__(self) -> str:
#         return self.name


# class Posts(BaseModel, models.Model):
#     """Product's Post"""
#     name = models.CharField(max_length=200)
#     description = models.CharField(max_length=300)

#     def __str__(self) -> str:
#         return self.name


class Product(BaseModel, models.Model):
    """Product Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=300, blank=False)
    quantity = models.IntegerField(blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=False)
    picture = models.ImageField(null=True, upload_to='inventory/images/', blank=True)
    # other_attr = models.ManyToManyField(AdditionalAttr, related_name='other_attr')
    # posts = models.ManyToManyField(Posts, related_name='')

    def total_price(self):
        """Returns Quantity times Price"""
        return self.quantity * self.price

    def __str__(self) -> str:
        return self.name
