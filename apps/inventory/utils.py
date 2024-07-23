from .models import User, Product, Category, Supplier, AddAttr, AddAttrDescription


def user_products_data(user: User) -> dict:
    """Return a dictionary of all necessary info that will be used in
    the register_item template"""
    custom_fields = ['category', 'supplier']
    products = Product.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    suppliers = Supplier.objects.filter(user=user)
    add_attributes = ['Color', 'Size', 'Style']
    query_user_add_attributes = AddAttr.objects.filter(user=user)
    user_add_attributes = [add_attr.name for add_attr in query_user_add_attributes]
    for add_attr in user_add_attributes:
        if add_attr not in add_attributes:
            add_attributes.append(add_attr)
    return {
        'custom_fields': custom_fields,
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'add_attributes': add_attributes
    }


def get_or_create_custom_fields(user: User, custom_fields: list, request_data: dict) -> dict:
    """Creates new Category/Supplier instances if not exists
    and adds the instances to the submitted form data"""
    form_data = request_data.copy()
    for field in custom_fields:
        field_name = request_data.get(field)
        if field_name:
            model = Category if field == 'category' else Supplier
            obj, created = model.objects.get_or_create(name=field_name)
            if created:
                obj.user = user
                obj.save()
            form_data[field] = obj.id
    return form_data


def add_additional_attr(user: User, product: Product, attr_num: int, request_post_data: dict) -> None:
    """Adds Additional Attributes with descriptions to the product"""
    for i in range(1, attr_num + 1):
        add_attr_name = request_post_data.get(f'add-attr-{i}')
        add_attr, created = AddAttr.objects.get_or_create(name=add_attr_name)
        if created:
            add_attr.user = user
            add_attr.save()
        add_attr_desc = request_post_data.get(f'add-attr-desc-{i}')
        AddAttrDescription.objects.create(
            product=product,
            add_attr=add_attr,
            body=add_attr_desc
        )
        product.other_attr.add(add_attr)