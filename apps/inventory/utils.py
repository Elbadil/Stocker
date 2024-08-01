from .models import User, Item, Category, Supplier, Variant, VariantOptions
from typing import Union, List
import json


def user_items_data(user: User) -> dict:
    """Return a dictionary of all necessary info that will be used in
    the register_item template"""
    custom_fields = ['category', 'supplier']
    items = Item.objects.filter(user=user)
    categories = Category.objects.filter(user=user)
    suppliers = Supplier.objects.filter(user=user)
    variants = ['Color', 'Size', 'Style']
    query_user_items_variants = Variant.objects.filter(user=user)
    user_items_variants = [variant.name for variant in query_user_items_variants]
    for variant in user_items_variants:
        if variant not in variants:
            variants.append(variant)
    return {
        'custom_fields': custom_fields,
        'items': items,
        'categories': categories,
        'suppliers': suppliers,
        'variants': variants
    }


def get_or_create_custom_fields(user: User, custom_fields: list, request_data: dict) -> dict:
    """Creates new Category/Supplier instances if not exists
    and adds the instances to the submitted form data"""
    form_data = request_data.copy()
    for field in custom_fields:
        field_name = request_data.get(field)
        if field_name:
            model = Category if field == 'category' else Supplier
            obj, created = model.objects.get_or_create(name=field_name, user=user)
            if created:
                obj.user = user
                obj.save()
            form_data[field] = obj.id
    return form_data


def add_item_variants(user: User, item: Item, variants_num: int, request_post_data: dict) -> None:
    """Adds Variants with options to the item"""
    for i in range(1, variants_num + 1):
        variant_name = request_post_data.get(f'variant-{i}')
        variant, created = Variant.objects.get_or_create(name=variant_name, user=user)
        if created:
            variant.user = user
            variant.save()
        variant_opts = request_post_data.get(f'variant-opt-{i}').split(',')
        print(f'Variant Options: {variant_opts}, {variant_opts}')
        for option in variant_opts:
            VariantOptions.objects.create(
                item=item,
                variant=variant,
                body=option.strip()
            )
        item.variants.add(variant)


def add_category_supplier_to_items(items_json: json, instance: Union[Category, Supplier]) -> str:
    """Adds a category or a supplier to a list of items"""
    items_ids = [id for id in json.loads(items_json)]
    if isinstance(instance, Category):
        Item.objects.filter(id__in=items_ids).update(category=instance, updated=True)
    else:
        Item.objects.filter(id__in=items_ids).update(supplier=instance, updated=True)


def set_items_table_display_data(items: List[Item]) -> dict:
    """Sets Necessary Data to be displayed in the Items Data Table"""
    items_total_prices = [item.total_price for item in items]
    items_quantities = [item.quantity for item in items]
    for item in items:
        item.created_at = item.created_at.strftime("%d/%m/%y")
        item.updated_at = item.updated_at.strftime("%d/%m/%y")
    items.total_value = sum(items_total_prices)
    items.total_quantity = sum(items_quantities)
