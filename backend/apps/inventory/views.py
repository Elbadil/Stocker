from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from ..base.auth import TokenVersionAuthentication
from . import serializers
from urllib.parse import urlencode
from .forms import ItemRegisterForm, CategoryRegisterForm, SupplierRegisterForm
from .models import Item, Category, Supplier, VariantOption
from .utils import (user_items_data,
                    get_or_create_custom_fields,
                    add_item_variants,
                    add_category_supplier_to_items,
                    set_items_table_display_data)
import json


class CreateItem(generics.CreateAPIView):
    """Handles Item's Creation"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ItemSerializer


class GetUpdateDeleteItem(generics.RetrieveUpdateDestroyAPIView):
    """Handles Item's Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Item.objects.all()
    serializer_class = serializers.ItemSerializer
    lookup_field = 'id'


class CreateCategory(generics.CreateAPIView):
    """Handles Item's Category Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CategorySerializer


class GetUpdateDeleteCategory(generics.RetrieveUpdateDestroyAPIView):
    """Handles Item's Category Retrieval Update and Deletion"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    lookup_field = 'id'


@login_required(login_url='login')
def inventory(request):
    """Inventory Home"""
    user = request.user
    items = Item.objects.filter(user=user)
    set_items_table_display_data(items)
    categories = Category.objects.filter(item__in=items).distinct()
    context = {
        'title': 'Inventory',
        'items': items,
        'categories': categories
    }
    return render(request, 'inventory.html', context)


@login_required(login_url='login')
def addItem(request):
    """Registers New Item"""
    user = request.user
    form = ItemRegisterForm(user=user)
    user_items_info = user_items_data(user)
    # Getting and filling the category/supplier field with a category/supplier
    # name if we recently created a category/supplier in the addCategory/addSupplier views
    category_name = request.GET.get('category_name')
    supplier_name = request.GET.get('supplier_name')

    if request.method == 'POST':
        # Creating new Category/Supplier instances if not exists
        # And Adding the instances to the submitted form data
        form_data = get_or_create_custom_fields(user,
                                                user_items_info['custom_fields'],
                                                request.POST)
        form = ItemRegisterForm(form_data, user=user)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = user
            if 'picture' in request.FILES:
                item.picture = request.FILES['picture']
            item.save()
            # Handling Item's Variants
            variants_num = request.POST.get('variants_num')
            if variants_num:
                add_item_variants(user, item, int(variants_num), request.POST)
            # Success Message
            messages.success(request,
                             f'Item <b>{item.name}</b> has been successfully added to your inventory!',
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
        'items': user_items_info['items'],
        'custom_fields': user_items_info['custom_fields'],
        'categories': user_items_info['categories'],
        'suppliers': user_items_info['suppliers'],
        'category_name': category_name,
        'supplier_name': supplier_name,
        'variants': json.dumps(user_items_info['variants'])
    }
    return render(request, 'register_item.html', context)


@login_required(login_url='login')
def editItem(request, item_id):
    """Updates an Exiting Item in the inventory"""
    item = get_object_or_404(Item, id=item_id, user=request.user)
    if request.user != item.user:
        return HttpResponse('Unauthorized')
    user = request.user
    form = ItemRegisterForm(instance=item, item=item, user=user)
    user_items_info = user_items_data(user)
    item_name = item.name

    if request.method == 'POST':
        form_data = get_or_create_custom_fields(user,
                                                user_items_info['custom_fields'],
                                                request.POST)
        form = ItemRegisterForm(form_data, instance=item, item=item, user=user)
        if form.is_valid():
            item = form.save(commit=False)
            item.updated = True
            if 'picture' in request.FILES:
                item.picture = request.FILES['picture']
            item.save()
            # Handling Item's Variants
            # Clearing old variants and options
            item.variants.clear()
            VariantOption.objects.filter(item=item).delete()
            variants_num = request.POST.get('variants_num')
            # Adding new variants if any
            if variants_num:
                add_item_variants(user, item, int(variants_num), request.POST)
            # Success Message
            messages.success(request,
                             f'Item <b>{item_name}</b> has been successfully updated!',
                             extra_tags='inventory')
            return JsonResponse({'success': True,
                                 'message': 'Form Submitted Successfully'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False,
                                 'errors': form.errors,
                                 'fields': form_fields})

    context = {
        'title': f'Edit Item - {item.name}',
        'form': form,
        'item': item,
        'custom_fields': user_items_info['custom_fields'],
        'categories': user_items_info['categories'],
        'suppliers': user_items_info['suppliers'],
        'variants': json.dumps(user_items_info['variants'])
    }
    return render(request, 'register_item.html', context)


@login_required(login_url='login')
def deleteItem(request, item_id):
    """Deletes an Existing Item From the inventory"""
    item = get_object_or_404(Item, id=item_id)
    if request.user != item.user:
        return HttpResponse('Unauthorized')
    item_name = item.name
    # deleting the selected item
    item.delete()
    messages.success(request,
                     f'Item <b>{item_name}</b> has been successfully deleted!',
                     extra_tags='inventory')
    return redirect('inventory_home')


@login_required(login_url='login')
def addCategory(request):
    """Adds a new Category with specified Items"""
    user = request.user
    items = Item.objects.filter(category__isnull=True, user=user)
    form = CategoryRegisterForm(user=user)

    if request.method == 'POST':
        form = CategoryRegisterForm(request.POST, user=user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            # Adding Selected items to the category if any
            json_category_items = request.POST.get('user_items')
            if json_category_items:
                add_category_supplier_to_items(json_category_items, category)
            # Generating a link that will be used in the Success Message
            add_item_url = reverse('add_item')
            category_name_query_params = urlencode({'category_name': category.name})
            add_item_url_with_params = f'{add_item_url}?{category_name_query_params}'
            messages.success(request,
                             f"""Category <b>{category.name}</b> has been successfully added. 
                             <b><a href={add_item_url_with_params}>Add {'more items' if json_category_items else 'items'} 
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
        'items' : items
    }
    return render(request, 'register_ctg_sup.html', context)


@login_required(login_url='login')
def addSupplier(request):
    """Adds a new Supplier with specified Items"""
    user = request.user
    items = Item.objects.filter(supplier__isnull=True, user=user)
    form = SupplierRegisterForm(user=user)

    if request.method == 'POST':
        form = SupplierRegisterForm(request.POST, user=user)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.user = user
            supplier.save()
            # Adding Selected items to the supplier if any
            json_supplier_items = request.POST.get('user_items')
            if json_supplier_items:
                add_category_supplier_to_items(json_supplier_items, supplier)
            # Generating a link that will be used in the Success Message
            add_item_url = reverse('add_item')
            supplier_name_query_params = urlencode({'supplier_name': supplier.name})
            add_item_url_with_params = f'{add_item_url}?{supplier_name_query_params}'
            # Success Message
            messages.success(request,
                             f"""Supplier <b>{supplier.name}</b> has been successfully added. 
                             <b><a href={add_item_url_with_params}>Add {'more items' if json_supplier_items else 'items'} 
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
        'items': items
    }
    return render(request, 'register_ctg_sup.html', context)


@login_required(login_url='login')
def itemsByCategory(request, category_name):
    """Filters items by a category"""
    user = request.user
    category = get_object_or_404(Category, name=category_name, user=user)
    items = Item.objects.filter(user=user, category__name=category.name)
    set_items_table_display_data(items)
    categories = Category.objects.filter(item__in=items).distinct()
    context = {
        'title': f'Items By Category - {category.name}',
        'table_title': f'<b>Items By Category: </b>{category.name}',
        'items': items,
        'category_id': category.id,
        'categories': categories
    }
    return render(request, 'inventory.html', context)


@login_required(login_url='login')
def itemsBySupplier(request, supplier_name):
    """Filters items by a supplier"""
    user = request.user
    supplier = get_object_or_404(Supplier, name=supplier_name, user=user)
    items = Item.objects.filter(user=user, supplier__name=supplier.name)
    set_items_table_display_data(items)
    categories = Category.objects.filter(item__in=items).distinct()
    context = {
        'title': f'Items By Supplier - {supplier.name}',
        'table_title': f'<b>Items By Supplier: </b>{supplier.name}',
        'items': items,
        'supplier_id': supplier.id,
        'categories': categories
    }
    return render(request, 'inventory.html', context)
