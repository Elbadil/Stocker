import uuid


class Token:
    """Generates and Validates Tokens"""
    @staticmethod
    def generate_uuid():
        """generates and returns a unique id"""
        return str(uuid.uuid4())

    @staticmethod
    def validate_uuids(ids):
        """Validate that all provided IDs are valid UUIDs."""
        invalid_ids = []
        for id_ in ids:
            try:
                uuid.UUID(str(id_))  # Attempt to convert to UUID
            except (ValueError, TypeError):
                invalid_ids.append(id_)
        return invalid_ids
