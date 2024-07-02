import random
import string
from datetime import datetime, timezone


def generate_random_number_string(length: int) -> str:
    """Generates a random number of a size of a given length"""
    digits = string.digits
    random_string = ''.join(random.choice(digits) for _ in range(length))
    return str(random_string)


def date_difference_in_minutes(token_created_at: datetime) -> float:
    """Calculates the difference a created_at datetime
    and now in minutes"""
    now = datetime.now(timezone.utc)
    # When you subtract one datetime object (token_created_at) from another (now)
    # Python automatically creates a timedelta object (difference).
    difference = now - token_created_at
    # total_seconds() Method: Converts the timedelta object to seconds
    difference_in_minutes = difference.total_seconds() / 60
    return difference_in_minutes
