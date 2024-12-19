from rest_framework.response import Response
from rest_framework import status
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
    """"""
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
