import random
import string
import uuid
from datetime import datetime, timezone


class Token:
    """Generates and Validates Tokens"""
    def generate_uuid():
        """generates and returns a unique id"""
        return str(uuid.uuid4())

    def generate_token_with_length(length: int) -> str:
        """Generates a token of a size of a given length"""
        digits = string.digits
        random_string = ''.join(random.choice(digits) for _ in range(length))
        return str(random_string)

    def validation(token_created_at: datetime, max_minutes: int) -> bool:
        """Checks if a token is valid by comparing the difference between
        a created_at datetime and now in minutes"""
        now = datetime.now(timezone.utc)
        # When you subtract one datetime object (token_created_at) from another (now)
        # Python automatically creates a timedelta object (difference).
        difference = now - token_created_at
        # total_seconds() Method: Converts the timedelta object to seconds
        difference_in_minutes = difference.total_seconds() / 60
        return True if difference_in_minutes < max_minutes else False
