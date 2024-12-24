from rest_framework import serializers
from typing import Any, Union, Optional, Callable, List
from deepdiff import DeepDiff
from apps.base.models import User
from apps.inventory.models import Item
from apps.client_orders.models import (Location,
                                       AcquisitionSource,
                                       OrderStatus,
                                       Client,
                                       ClientOrder,
                                       ClientOrderedItem)
from apps.supplier_orders.models import (Supplier,
                                         SupplierOrder,
                                         SupplierOrderedItem)
from apps.sales.models import Sale, SoldItem


def datetime_repr_format(datetime) -> str:
    """Returns the correct format for datetime data representation"""
    return datetime.strftime('%d/%m/%Y')

def get_or_create_source(
    user: User,
    value: str
) -> Union[AcquisitionSource, None]:
    """Handles source of acquisition creation"""
    if value:
        acq_source, created = AcquisitionSource.objects.get_or_create(
            added_by__isnull=True,
            name__iexact=value,
            defaults={'added_by': user,
                      'name': value}
        )
        return acq_source
    return None

def get_or_create_location(
    user: User,
    data: dict,
) -> Union[Location, None]:
    """Handles location creation"""
    from apps.client_orders.serializers import LocationSerializer

    if data:
        serializer = LocationSerializer(data=data,
                                        context={'user': user})
        if serializer.is_valid():
            obj = serializer.save()
            return obj
        else:
            raise serializers.ValidationError(serializer.errors)
    return None

def get_location(instance_attribute: Location) -> Union[dict, None]:
    """Returns the correct format for location data representation"""
    if instance_attribute:
        return {
            'country': instance_attribute.country.name,
            'city': instance_attribute.city.name,
            'street_address': instance_attribute.street_address,
        }
    return None

def update_item_quantity(
    item: Item,
    old_ordered_quantity: int,
    new_ordered_quantity: int
) -> int:
    """returns item inventory's new quantity after update"""
    if old_ordered_quantity == new_ordered_quantity:
        return item.quantity
    quantity_diff = new_ordered_quantity - old_ordered_quantity
    return item.quantity - quantity_diff

def handle_null_fields(fields: dict) -> dict:
    """Sets frontend FormData object's null field values to None"""
    for key, value in fields.items():
        if value == 'null':
            fields[key] = None
    return fields

def update_field(
    self,
    instance,
    field_name: str,
    value: Optional[Any],
    create_func: Optional[Callable] = None,
    user: Optional[User] = None
) -> None:
    """Updates instance field value with optional creation function"""
    if value:
        if create_func and user:
            setattr(instance, field_name, create_func(user, value))
        else:
            setattr(instance, field_name, value)
    elif field_name in self.initial_data:
        setattr(instance, field_name, None)

def check_item_existence(
    item_model: Union[ClientOrderedItem, SupplierOrderedItem, SoldItem],
    parent_instance: Union[ClientOrder, SupplierOrder, Sale],
    item_name: str,
    instance: Union[ClientOrderedItem, SupplierOrderedItem, SoldItem, None]=None,
) -> bool: 
    """
    Checks for an already existing item with the same name in the list of 
    sale's/order's items.
    returns:
        True if an item with the same name exists, otherwise False.
    """
    parent_field = 'sale' if isinstance(parent_instance, Sale) else 'order'

    query = {
        parent_field: parent_instance,
        'item__name__iexact': item_name
    }

    if instance:
        return item_model.objects.filter(**query).exclude(id=instance.id).exists()

    return item_model.objects.filter(**query).exists()


def restricted_fields_have_changes(
    prev_values: dict,
    new_values: dict
) -> List:
    """Returns changed fields between prev and new values"""
    changed_fields = []
    diff = DeepDiff(prev_values, new_values, ignore_order=True)
    if diff:
        values_changed = diff.get('values_changed', {})
        changed_fields = [key.split("'")[1] for key in values_changed.keys()]
    return changed_fields


def validate_restricted_fields(
    instance: Union[SupplierOrder,ClientOrder, Sale],
    instance_data: dict,
    participant: Union[Client, Supplier],
    items: Union[List[dict], None],
    keys_to_remove_from_items: List[str],
    delivery_status: Union[OrderStatus, None],
) -> None:
    """
    Raises a validation error if any changes have been made to restricted fields
    """
    items_name = 'sold_items' if isinstance(instance, Sale) else 'ordered_items'
    party = 'supplier' if isinstance(participant, Supplier) else 'client'

    prev_items = []
    for item in instance_data[items_name]:
        prev_items.append({key: value for key,
                           value in item.items()
                           if key not in keys_to_remove_from_items})
    prev_values = {
        party: instance_data[party],
        items_name: prev_items,
        'delivery_status': instance_data['delivery_status']
    }

    new_values = {
        party: participant.name,
        items_name: items if items else prev_items,
        'delivery_status': (delivery_status.name
                            if delivery_status
                            else instance.delivery_status.name),
    }

    changed_fields = restricted_fields_have_changes(prev_values, new_values)

    instance_in_error_message = (
        'sale is linked to a client order and'
        if isinstance(instance, Sale) else 'order'
    )

    if changed_fields:
        raise serializers.ValidationError({
            'error': {
                'message': f'This {instance_in_error_message} and '
                            'has already been marked as delivered. '
                            'Restricted fields cannot be modified.',
                'restricted_fields': changed_fields,
            }
        })

def validate_changes_for_delivered_parent_instance(
    parent_instance: Union[SupplierOrder, ClientOrder, Sale]
) -> None:
    """
    Raises a validation error if the linked parent instance
    of the items has already been set to delivered
    """
    if isinstance(parent_instance, Sale):
        parent_instance_name = 'sale'
        items_name = 'sold items'
    else:
        parent_instance_name = 'order'
        items_name = 'ordered items'

    if parent_instance.delivery_status.name == 'Delivered':
        raise serializers.ValidationError({
            'error': (
                f"Cannot apply changes to the {parent_instance_name} "
                f"with reference ID '{parent_instance.reference_id}' "
                f"{items_name} because it has already been marked as "
                f"Delivered. Changes to delivered {parent_instance_name}s "
                "are restricted to maintain data integrity."
            )
        })