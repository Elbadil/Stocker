
class CreatedByUserMixin:
    """
    Mixin to ensure the queryset is filtered by created_by=request.user.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)
