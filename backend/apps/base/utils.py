import calendar
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.functions import ExtractIsoWeekDay, ExtractDay
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from typing import Union, List
from itertools import chain
from .models import User
from apps.sales.models import Sale
from apps.client_orders.models import ClientOrder


DAY_NAMES = {
    1: 'Mon',
    2: 'Tue',
    3: 'Wed',
    4: 'Thu',
    5: 'Fri',
    6: 'Sat',
    7: 'Sun',
}

def get_tokens_for_user(user: User) -> dict:
    """Adds more user data to the access jwt"""
    refresh = RefreshToken.for_user(user)
    refresh['token_version'] = user.token_version

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

def make_aware_datetime(datetime: datetime):
    """Turns a naive datetime into an aware one"""
    return timezone.make_aware(datetime, timezone.get_current_timezone())

def generate_filter_info(filter: str) -> Union[dict, Response]:
    """Returns necessary filtering data for a specific period"""
    today = date.today()
    year = today.year
    month = today.month

    if filter == 'week':
        categories = list(DAY_NAMES.values())
        start_of_week = datetime.combine(
            datetime.today() - timedelta(days=today.weekday()),
            time.min
        )
        end_of_week = datetime.combine(start_of_week + timedelta(days=6),
                                        time.max)
        date_range = (start_of_week.strftime("%d.%m.%Y") 
                    + ' - ' + end_of_week.strftime("%d.%m.%Y"))
        
        initial_days_map = {day: 0 for day in range(1, 8)}
        initial_revenue_per_day_map = {
            day: {'cost': 0, 'profit': 0} for day in range(1, 8)
        }
        date_type_query = {'day': ExtractIsoWeekDay('created_at')}

        created_at_range = (
            make_aware_datetime(start_of_week),
            make_aware_datetime(end_of_week)
        )

    elif filter == 'month':
        _, last_day = calendar.monthrange(year, month)

        categories = [
            date(year, month, day).strftime("%d.%m.%Y")
            for day in range(1, last_day + 1)
        ]

        start_of_month = datetime.combine(datetime(year, month, 1), time.min)
        end_of_month = datetime.combine(datetime(year, month, last_day), time.max)
        date_range = categories[0] + ' - ' + categories[-1] 

        initial_days_map = {day: 0 for day in range(1, last_day + 1)}
        initial_revenue_per_day_map = {
            day: {'cost': 0, 'profit': 0} for day in range(1, last_day + 1)
        }
        date_type_query = {'day': ExtractDay('created_at')}

        created_at_range = (
            make_aware_datetime(start_of_month),
            make_aware_datetime(end_of_month)
        )

    else:
        return Response(
            {'error': 'period parameter must be either week or month.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return {
        'categories': categories,
        'date_range': date_range,
        'initial_days_map': initial_days_map,
        'initial_revenue_per_day_map': initial_revenue_per_day_map,
        'date_type_query': date_type_query,
        'created_at_range': created_at_range
    }

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

def revenue_per_day(
    sales: List[Sale],
    date_type_query: dict,
    initial_revenue_per_day_map: dict
) -> dict:
    """Returns a dictionary that contains the Sales costs and profits per day"""
    sale_records_days = (
        sales
        .annotate(**date_type_query)
    )

    sales_revenue_per_day = initial_revenue_per_day_map.copy()

    for sale in sale_records_days:
        if sale.day in sales_revenue_per_day:
            sales_revenue_per_day[sale.day]['cost'] += sale.total_cost
            sales_revenue_per_day[sale.day]['profit'] += sale.net_profit

    return sales_revenue_per_day
