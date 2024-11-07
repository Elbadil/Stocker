from django.db import models
from .tokens import Token


class BaseModel(models.Model):
    """Base Model"""
    id = models.UUIDField(default=Token.generate_uuid,
                          unique=True, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures this model is abstract and not created as a table
        abstract = True
        ordering = ['-created_at']
