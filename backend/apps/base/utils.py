from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from typing import Union, List, Dict
from itertools import chain
from .models import User
from apps.sales.models import Sale
from apps.client_orders.models import ClientOrder


def get_tokens_for_user(user: User) -> dict:
    """Adds more user data to the access jwt"""
    refresh = RefreshToken.for_user(user)
    refresh.payload['token_version'] = user.token_version

    return {
        'refresh': str(refresh),
        'refresh_payload': refresh.payload,
        'access': str(refresh.access_token)
    }


def set_refresh_token(response, token: str, token_payload: dict) -> None:
    """Sets a refresh token as an HTTP-only cookie in the response"""
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite='Lax',
        expires=token_payload['exp'],
        max_age=token_payload['exp'] - datetime.now().timestamp(),
    )

def make_aware_datetime(datetime):
    """Turns a naive datetime into an aware one"""
    return timezone.make_aware(datetime, timezone.get_current_timezone())


def records_per_day(
    query: Union[dict, Q],
    initial_days_map: dict,
    date_type_query: dict,
    sales: List[Sale],
    orders: Union[List[ClientOrder], None]=None, 
) -> dict:
    """Returns a dictionary that contains the amount of records per day"""
    sales_queryset = (sales.filter(query)
                      if isinstance(query, Q)
                      else sales.filter(**query))

    sale_records_days = (
        sales_queryset
        .annotate(**date_type_query)
        .values('day')
    )

    if orders:
        orders_queryset = (orders.filter(query)
                           if isinstance(query, Q)
                           else orders.filter(**query))
        order_records_days = (
            orders_queryset
            .annotate(**date_type_query)
            .values('day')
        )
        records_days = chain(sale_records_days, order_records_days)
    else:
        records_days = sale_records_days

    records_per_day = initial_days_map.copy()
    for day in records_days:
        if day['day'] in records_per_day:
            records_per_day[day['day']] += 1

    return records_per_day
