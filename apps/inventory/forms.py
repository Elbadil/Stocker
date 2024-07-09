from django.forms import ModelForm
from apps.base.forms import AddFormControlClassMixin
from .models import Product, AddAttrDescription


class ProductRegisterForm(AddFormControlClassMixin, ModelForm):
    """Product Register Form"""
    class Meta:
        model = Product
        fields = [
            'name',
            'quantity',
            'price',
            'category',
            'supplier'
        ]


class AddAttrDescForm(AddFormControlClassMixin, ModelForm):
    """Product Register Form"""
    class Meta:
        model = AddAttrDescription
        fields = ['body']