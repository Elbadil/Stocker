from django.contrib.contenttypes.models import ContentType
from apps.base.models import Activity, User
from typing import Literal, Any


def register_activity(
    user: User,
    action: Literal["created", "updated", "deleted"],
    model_name: str,
    model: Any,
    instance_id: str
) -> Activity:
    """Registers and returns the newly created activity instance"""
    model_content_type = ContentType.objects.get_for_model(model)
    return Activity.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        content_type=model_content_type,
        object_id=instance_id
    )
