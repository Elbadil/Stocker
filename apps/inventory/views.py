from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from urllib.parse import urlencode
from .forms import ProductRegisterForm, CategoryRegisterForm, SupplierRegisterForm
from .models import Product, Category, Supplier
from .utils import (user_products_data,
                    get_or_create_custom_fields,
                    add_additional_attr,
                    add_category_supplier_to_products,
                    set_products_table_display_data)
import json


@login_required(login_url='login')
def listItems(request):
    """Inventory Home"""
    user = request.user
    products = Product.objects.filter(user=user)
    set_products_table_display_data(products)
    categories = Category.objects.filter(product__in=products).distinct()
    context = {
        'title': 'Inventory',
        'products': products,
        'categories': categories
    }
    return render(request, 'inventory.html', context)


@login_required(login_url='login')
def addItem(request):
    """Registers New Item"""
    user = request.user
    form = ProductRegisterForm(user=user)
    user_products_info = user_products_data(user)
    # Getting and filling the category/supplier field with a category/supplier
    # name if we recently created a category/supplier in the addCategory/addSupplier views
    category_name = request.GET.get('category_name')
    supplier_name = request.GET.get('supplier_name')

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
        'supplier_name': supplier_name,
        'add_attributes': json.dumps(user_products_info['add_attributes'])
    }
    return render(request, 'register_item.html', context)


@login_required(login_url='login')
def editItem(request, product_id):
    """Updates an Exiting Item in the inventory"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
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
            product.updated = True
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
            # Adding Selected products to the category if any
            json_category_products = request.POST.get('user_products')
            if json_category_products:
                add_category_supplier_to_products(json_category_products, category)
            # Generating a link that will be used in the Success Message
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
    return render(request, 'register_ctg_sup.html', context)


@login_required(login_url='login')
def addSupplier(request):
    """Adds a new Supplier with specified Items"""
    user = request.user
    products = Product.objects.filter(supplier__isnull=True, user=user)
    form = SupplierRegisterForm(user=user)

    if request.method == 'POST':
        form = SupplierRegisterForm(request.POST, user=user)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.user = user
            supplier.save()
            # Adding Selected products to the supplier if any
            json_supplier_products = request.POST.get('user_products')
            if json_supplier_products:
                add_category_supplier_to_products(json_supplier_products, supplier)
            # Generating a link that will be used in the Success Message
            add_item_url = reverse('add_item')
            supplier_name_query_params = urlencode({'supplier_name': supplier.name})
            add_item_url_with_params = f'{add_item_url}?{supplier_name_query_params}'
            # Success Message
            messages.success(request,
                             f"""Supplier <b>{supplier.name}</b> has been successfully added. 
                             <b><a href={add_item_url_with_params}>Add {'more items' if json_supplier_products else 'items'} 
                             with this Supplier</a></b>.""",
                             extra_tags='inventory')
            return JsonResponse({'success': True,
                                 'message': 'Supplier Form has been successfully submitted!'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False,
                                 'errors': form.errors,
                                 'fields': form_fields})
    context = {
        'title': 'Add Supplier',
        'form': form,
        'products': products
    }
    return render(request, 'register_ctg_sup.html', context)


@login_required(login_url='login')
def itemsByCategory(request, category_name):
    """Filters items by a category"""
    user = request.user
    category = get_object_or_404(Category, name=category_name, user=user)
    products = Product.objects.filter(user=user, category__name=category.name)
    set_products_table_display_data(products)
    categories = Category.objects.filter(product__in=products).distinct()
    context = {
        'title': f'Items By Category - {category.name}',
        'table_title': f'<b>Items By Category: </b>{category.name}',
        'products': products,
        'categories': categories
    }
    return render(request, 'inventory.html', context)


@login_required(login_url='login')
def itemsBySupplier(request, supplier_name):
    """Filters items by a supplier"""
    user = request.user
    supplier = get_object_or_404(Supplier, name=supplier_name, user=user)
    products = Product.objects.filter(user=user, supplier__name=supplier.name)
    set_products_table_display_data(products)
    categories = Category.objects.filter(product__in=products).distinct()
    context = {
        'title': f'Items By Supplier - {supplier.name}',
        'table_title': f'<b>Items By Supplier: </b>{supplier.name}',
        'products': products,
        'categories': categories
    }
    return render(request, 'inventory.html', context)
