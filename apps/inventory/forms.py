from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.base.forms import AddFormControlClassMixin
from .models import Product, Category


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

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        product_name = self.cleaned_data['name']
        exiting_product = Product.objects.filter(name__iexact=product_name,
                                                  user=self.user).exclude(pk=self.product.id
                                                                          if self.product
                                                                          else None).first()
        if exiting_product:
            # The reverse function will return the constructed URL as a string
            edit_url = reverse('edit_item', kwargs={'product_id': exiting_product.id})
            raise ValidationError(f"""Product with this name already exists.
                                   <a href="{edit_url}">Update {exiting_product.name}</a>""")
        return product_name


class CategoryRegisterForm(AddFormControlClassMixin, ModelForm):
    """Product Category Register Form"""
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('product', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        category_name = self.cleaned_data['name']
        if Category.objects.filter(name__iexact=category_name,
                                               user=self.user).exclude(pk=self.category.id
                                                                       if self.category
                                                                       else None).exists():
            raise ValidationError('Category with this name already exists.')
        return category_name