from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .forms import ProductRegisterForm
from .models import Product, Category, Supplier, AddAttr, AddAttrDescription
import json


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
    query_add_attributes = AddAttr.objects.all()
    add_attributes = [add_attr.name for add_attr in query_add_attributes]

    if request.method == 'POST':
        form_data = request.POST.copy()
        # Creating new Category/Supplier instance if not exists
        for field in custom_fields:
            field_name = request.POST.get(field)
            if field_name:
                model = Category if field == 'category' else Supplier
                obj, created = model.objects.get_or_create(name=field_name)
                form_data[field] = obj.id

        form = ProductRegisterForm(form_data)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = user
            if 'picture' in request.FILES:
                product.picture = request.FILES['picture']
            product.save()
            # Handling Additional Attributes
            get_attr_num = request.POST.get('attr_num')
            if get_attr_num:
                attr_num = int(get_attr_num)
                if attr_num > 0:
                    for i in range(1, attr_num + 1):
                        add_attr_name = request.POST.get(f'add-attr-{i}')
                        add_attr, created = AddAttr.objects.get_or_create(name=add_attr_name)
                        add_attr_desc = request.POST.get(f'add-attr-desc-{i}')
                        AddAttrDescription.objects.create(
                            product=product,
                            add_attr=add_attr,
                            body=add_attr_desc
                        )
                        product.other_attr.add(add_attr)
            messages.success(request,
                             f'{product.name} has been successfully added to your inventory',
                             extra_tags='inventory')
            return JsonResponse({'success': True, 'message': 'Form Submitted Successfully'})
        else:
            form_fields = [name for name in form.fields.keys()]
            return JsonResponse({'success': False, 'errors': form.errors, 'fields': form_fields})

    context = {
        'title': 'Inventory - Add Item',
        'form': form,
        'custom_fields': custom_fields,
        'categories': categories,
        'suppliers': suppliers,
        'add_attributes': json.dumps(add_attributes)
    }
    return render(request, 'register_item.html', context)