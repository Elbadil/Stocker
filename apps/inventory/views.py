from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .forms import ProductRegisterForm
from .models import Product, Category, Supplier, AddAttr, AddAttrDescription
from .utils import user_products_info, add_additional_attr
import json


@login_required(login_url='login')
def listItems(request):
    """Inventory Home"""
    user = request.user
    products = Product.objects.filter(user=user)
    context = {
        'title': 'Inventory',
        'products': products
    }
    return render(request, 'inventory.html', context)


@login_required(login_url='login')
def addItem(request):
    """Registers New Item"""
    user = request.user
    form = ProductRegisterForm(user=user)
    products_info = user_products_info(user)

    if request.method == 'POST':
        form_data = request.POST.copy()
        # Creating new Category/Supplier instance if not exists
        for field in products_info['custom_fields']:
            field_name = request.POST.get(field)
            if field_name:
                model = Category if field == 'category' else Supplier
                obj, created = model.objects.get_or_create(name=field_name)
                form_data[field] = obj.id

        form = ProductRegisterForm(form_data, user=user)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = user
            if 'picture' in request.FILES:
                product.picture = request.FILES['picture']
            product.save()
            # Handling Additional Attributes
            attr_num = request.POST.get('attr_num')
            if attr_num:
                add_additional_attr(product, int(attr_num), request.POST)
            # Success Message
            messages.success(request,
                             f'{product.name} has been successfully added to your inventory',
                             extra_tags='inventory')
            return JsonResponse({'success': True,
                                 'message': 'Form Submitted Successfully'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False,
                                 'errors': form.errors,
                                 'fields': form_fields})

    context = {
        'title': 'Add Item',
        'form': form,
        'products': products_info['products'],
        'custom_fields': products_info['custom_fields'],
        'categories': products_info['categories'],
        'suppliers': products_info['suppliers'],
        'add_attributes': json.dumps(products_info['add_attributes'])
    }
    return render(request, 'register_item.html', context)


@login_required(login_url='login')
def editItem(request, product_id):
    """Updates an Exiting Item in the inventory"""
    product = get_object_or_404(Product, id=product_id)
    if request.user != product.user:
        return HttpResponse('Unauthorized')
    user = request.user
    form = ProductRegisterForm(instance=product, product=product, user=user)
    products_info = user_products_info(user)
    product_name = product.name

    if request.method == 'POST':
        form_data = request.POST.copy()
        # Creating new Category/Supplier instance if not exists
        for field in products_info['custom_fields']:
            field_name = request.POST.get(field)
            if field_name:
                model = Category if field == 'category' else Supplier
                obj, created = model.objects.get_or_create(name=field_name)
                form_data[field] = obj.id

        form = ProductRegisterForm(form_data, instance=product, product=product, user=user)
        if form.is_valid():
            product = form.save(commit=False)
            if 'picture' in request.FILES:
                product.picture = request.FILES['picture']
            product.save()
            # Handling Additional Attributes
            # Clearing old other_attr and descriptions
            product.other_attr.clear()
            product.addattrdescription_set.all().delete()
            attr_num = request.POST.get('attr_num')
            # Adding new additional attributes if any
            if attr_num:
                add_additional_attr(product, int(attr_num), request.POST)
            # Success Message
            messages.success(request,
                             f'{product_name} has been successfully updated!',
                             extra_tags='inventory')
            return JsonResponse({'success': True,
                                 'message': 'Form Submitted Successfully'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False,
                                 'errors': form.errors,
                                 'fields': form_fields})

    context = {
        'title': f'Edit Item - {product.name}',
        'form': form,
        'product': product,
        'custom_fields': products_info['custom_fields'],
        'categories': products_info['categories'],
        'suppliers': products_info['suppliers'],
        'add_attributes': json.dumps(products_info['add_attributes'])
    }
    return render(request, 'register_item.html', context)
