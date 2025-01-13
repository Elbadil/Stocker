from apps.base.models import Activity, User
from typing import List, Literal, Union


def register_activity(
    user: User,
    action: Literal["created", "updated", "deleted"],
    model_name: str,
    object_ref: List[str],
) -> Activity:
    """Registers and returns a new activity instance"""
    return Activity.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_ref=object_ref
    )
