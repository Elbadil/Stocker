from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db.models import CharField
from django.db.models.functions import Cast
from typing import Union, List
from apps.client_orders.models import ClientOrder, ClientOrderedItem
from apps.supplier_orders.models import SupplierOrder, SupplierOrderedItem
from apps.sales.models import Sale, SoldItem
from .tokens import Token


class CreatedByUserMixin:
    """
    Mixin to ensure the queryset is filtered by created_by=request.user.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)


def validate_linked_items_for_deletion(
    ids: List[str],
    queryset: List[Union[ClientOrderedItem, SupplierOrderedItem, SoldItem]],
    parent_model: Union[ClientOrder, SupplierOrder, Sale],
) -> Union[Response, tuple]:
    """
    Validates whether the given items can be deleted.
    returns:
        Response object with error message if validation fails
        Else a (parent_instance, items_for_deletion) tuple
    """
    # Validate ids
    if not ids:
        return Response({'error': 'No IDs provided.'},
                        status=status.HTTP_400_BAD_REQUEST)

    invalid_uuids = Token.validate_uuids(ids)
    if invalid_uuids:
        return Response(
            {
                'error': {
                    'message': 'Some or all provided IDs are not valid uuids.',
                    'invalid_uuids': invalid_uuids
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Query items for deletion
    items_for_deletion = queryset.filter(id__in=ids)

    # Check for missing ids
    items_ids = set(
        items_for_deletion
        .annotate(id_str=Cast('id', CharField()))
        .values_list('id_str', flat=True)
    )
    missing_ids = set(ids) - items_ids
    if missing_ids:
        return Response(
            {
                'error': {
                    'message': 'Some or all provided IDs are not found.',
                    'missing_ids': list(missing_ids)
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Prevent deleting all items from a sale
    if parent_model == Sale:
        parent_instance = items_for_deletion.first().sale
        parent_instance_str = 'sale'
    else:
        parent_instance = items_for_deletion.first().order
        parent_instance_str = 'order'

    if parent_instance.items.count() == items_for_deletion.count():
        parent_instance_ref_id = parent_instance.reference_id
        return Response(
            {
                'error': (
                    f"Cannot delete items from {parent_instance_str} with reference ID "
                    f"'{parent_instance_ref_id}' as it would leave no items linked. "
                    "Each sale must have at least one item."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Return parent instance and items for deletion
    # to perform deletion in its custom view
    return (parent_instance, items_for_deletion)


def validate_deletion_for_delivered_parent_instance(
    parent_instance: Union[ClientOrder, SupplierOrder, Sale]
) -> Union[Response, None]:
    """
    Returns a response with an error message if the linked parent
    instance of the items has already been set to delivered
    """
    if isinstance(parent_instance, Sale):
        parent_instance_name = 'sale'
        items_name = 'sold items'
    else:
        parent_instance_name = 'order'
        items_name = 'ordered items'

    if parent_instance.delivery_status.name == 'Delivered':
        return Response({
            'error': (
                f"Cannot perform item deletion because the {parent_instance_name} "
                f"with reference ID '{parent_instance.reference_id}' has "
                "already been marked as Delivered. Changes to delivered "
                f"{parent_instance_name}s' {items_name} are restricted to "
                "maintain data integrity."
            )},
            status=status.HTTP_400_BAD_REQUEST
        )
