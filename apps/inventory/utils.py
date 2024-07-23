from .models import User, Product, Category, Supplier, AddAttr, AddAttrDescription


def user_products_info(user: User) -> dict:
    """Return a dictionary of all necessary info that will be used in
    the register_item template"""
    custom_fields = ['category', 'supplier']
    products = Product.objects.filter(user=user)
    # retrieves categories/suppliers where the related product is in
    # the products queryset obtained from the user's products.
    categories = Category.objects.filter(product__in=products).distinct()
    # .distinct() ensures that each category appears only once in
    # the queryset, even if it's associated with multiple products.
    suppliers = Supplier.objects.filter(product__in=products).distinct()
    query_add_attributes = AddAttr.objects.all()
    add_attributes = [add_attr.name for add_attr in query_add_attributes]
    return {
        'custom_fields': custom_fields,
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'add_attributes': add_attributes
    }


def add_additional_attr(product: Product, attr_num: int, request_post_data: dict) -> None:
    """Adds Additional Attributes with descriptions to the product"""
    for i in range(1, attr_num + 1):
        add_attr_name = request_post_data.get(f'add-attr-{i}')
        add_attr, created = AddAttr.objects.get_or_create(name=add_attr_name)
        add_attr_desc = request_post_data.get(f'add-attr-desc-{i}')
        AddAttrDescription.objects.create(
            product=product,
            add_attr=add_attr,
            body=add_attr_desc
        )
        product.other_attr.add(add_attr)
