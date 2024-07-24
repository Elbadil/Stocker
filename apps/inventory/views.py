from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from urllib.parse import urlencode
from .forms import ProductRegisterForm, CategoryRegisterForm
from .models import Product, Category, Supplier
from .utils import user_products_data, get_or_create_custom_fields, add_additional_attr
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
    user_products_info = user_products_data(user)
    # Getting and filling the category field with a category name
    # if we recently created a category in the addCategory view
    category_name = request.GET.get('category_name')

    if request.method == 'POST':
        # Creating new Category/Supplier instances if not exists
        # And Adding the instances to the submitted form data
        form_data = get_or_create_custom_fields(user,
                                                user_products_info['custom_fields'],
                                                request.POST)
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
                add_additional_attr(user, product, int(attr_num), request.POST)
            # Success Message
            messages.success(request,
                             f'Item <b>{product.name}</b> has been successfully added to your inventory!',
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
        'products': user_products_info['products'],
        'custom_fields': user_products_info['custom_fields'],
        'categories': user_products_info['categories'],
        'suppliers': user_products_info['suppliers'],
        'category_name': category_name,
        'add_attributes': json.dumps(user_products_info['add_attributes'])
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
    user_products_info = user_products_data(user)
    product_name = product.name

    if request.method == 'POST':
        form_data = get_or_create_custom_fields(user,
                                                user_products_info['custom_fields'],
                                                request.POST)
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
                add_additional_attr(user, product, int(attr_num), request.POST)
            # Success Message
            messages.success(request,
                             f'Item <b>{product_name}</b> has been successfully updated!',
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
        'custom_fields': user_products_info['custom_fields'],
        'categories': user_products_info['categories'],
        'suppliers': user_products_info['suppliers'],
        'add_attributes': json.dumps(user_products_info['add_attributes'])
    }
    return render(request, 'register_item.html', context)


@login_required(login_url='login')
def deleteItem(request, product_id):
    """Deletes an Existing Item From the inventory"""
    product = get_object_or_404(Product, id=product_id)
    if request.user != product.user:
        return HttpResponse('Unauthorized')
    product_name = product.name
    # deleting the selected product
    product.delete()
    messages.success(request,
                     f'Item <b>{product_name}</b> has been successfully deleted!',
                     extra_tags='inventory')
    return redirect('inventory_home')


@login_required(login_url='login')
def addCategory(request):
    """Adds a new Category with specified Items"""
    user = request.user
    products = Product.objects.filter(category__isnull=True, user=user)
    form = CategoryRegisterForm(user=user)

    if request.method == 'POST':
        form = CategoryRegisterForm(request.POST, user=user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            # Adding Selected products to the category
            json_category_products = request.POST.get('category_products')
            if json_category_products:
                category_products_ids = json.loads(json_category_products)
                for product_id in category_products_ids:
                    product = Product.objects.get(id=product_id)
                    product.category = category
                    product.save()
            # Success Message
            add_item_url = reverse('add_item')
            category_name_query_params = urlencode({'category_name': category.name})
            add_item_url_with_params = f'{add_item_url}?{category_name_query_params}'
            messages.success(request,
                             f"""Category <b>{category.name}</b> has been successfully added. 
                             <b><a href={add_item_url_with_params}>Add {'more items' if json_category_products else 'items'} 
                             to this Category</a></b>.""",
                             extra_tags='inventory')
            return JsonResponse({'success': True,
                                 'message': 'Category Form has been successfully submitted!'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False,
                                 'errors': form.errors,
                                 'fields': form_fields})
    context = {
        'title': 'Add Category',
        'form': form,
        'products' : products
    }
    return render(request, 'register_category.html', context)
