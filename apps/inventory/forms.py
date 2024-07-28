from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.base.forms import AddFormControlClassMixin
from .models import Item, Category, Supplier


class ItemRegisterForm(AddFormControlClassMixin, ModelForm):
    """Product Register Form"""
    class Meta:
        model = Item
        fields = [
            'name',
            'quantity',
            'price',
            'category',
            'supplier'
        ]

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        item_name = self.cleaned_data['name']
        exiting_item = Item.objects.filter(name__iexact=item_name,
                                                  user=self.user).exclude(pk=self.item.id
                                                                          if self.item
                                                                          else None).first()
        if exiting_item:
            # The reverse function will return the constructed URL as a string
            edit_url = reverse('edit_item', kwargs={'item_id': exiting_item.id})
            raise ValidationError(f"""Item with this name already exists.
                                   <a href="{edit_url}">Update {exiting_item.name}</a>""")
        return item_name


class CategoryRegisterForm(AddFormControlClassMixin, ModelForm):
    """Product Category Register Form"""
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
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


class SupplierRegisterForm(AddFormControlClassMixin, ModelForm):
    """Product Supplier Register Form"""
    class Meta:
        model = Supplier
        fields = [
            'name',
            'phone_number'
        ]

    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        supplier_name = self.cleaned_data['name']
        if Supplier.objects.filter(name__iexact=supplier_name,
                                               user=self.user).exclude(pk=self.supplier.id
                                                                       if self.supplier
                                                                       else None).exists():
            raise ValidationError('Supplier with this name already exists.')
        return supplier_name
