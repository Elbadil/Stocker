from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.forms import inlineformset_factory
from .forms import ProductRegisterForm
from .models import Product, Category, Supplier


@login_required(login_url='login')
def home(request):
    """Inventory Home"""
    context = {'title': 'Inventory'}
    return render(request, 'home.html', context)


@login_required(login_url='login')
def addItem(request):
    """Registers New Item"""
    user = request.user
    form = ProductRegisterForm()
    custom_fields = ['category', 'supplier']
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        form_data = request.POST.copy()
        # Creating new Category/Supplier instance if not exists
        for field in custom_fields:
            field_name = request.POST.get(field)
            if field_name:
                model = Category if field == 'category' else Supplier
                obj, created = model.objects.get_or_create(name=field_name)
                form_data[field] = obj.id

        form = ProductRegisterForm(form_data, request.FILES)

        if form.is_valid():
            product = form.save(commit=False)
            product.user = user
            product.save()
            messages.success(request,
                             f'{product.name} has been successfully added to your inventory',
                             extra_tags='inventory')
            return redirect('inventory_home')

    context = {
        'title': 'Inventory - Add Item',
        'form': form,
        'custom_fields': custom_fields,
        'categories': categories,
        'suppliers': suppliers
    }
    return render(request, 'register_item.html', context)