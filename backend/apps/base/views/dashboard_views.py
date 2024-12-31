from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.db.models.functions import ExtractIsoWeekDay, ExtractDay
from datetime import datetime, timedelta, date, time
import calendar
from ..auth import TokenVersionAuthentication
from apps.inventory.models import Item
from apps.client_orders.models import ClientOrder
from apps.sales.models import Sale
from utils.views import CreatedByUserMixin
from ..utils import make_aware_datetime, records_per_day
from utils.status import (ACTIVE_DELIVERY_STATUS,
                          ACTIVE_PAYMENT_STATUS,
                          FAILED_STATUS)


class GetDashboardInfo(generics.GenericAPIView):
    """Return necessary data related to the user's dashboard"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = self.request.user
        total_items_quantities = (
            Item.objects
            .filter(
                created_by=user,
                in_inventory=True
            )
            .aggregate(total_quantity=Sum('quantity'))
        )['total_quantity']

        total_sales = Sale.objects.filter(created_by=user)
        client_orders = ClientOrder.objects.filter(created_by=user)

        active_query = {
            'delivery_status__name__in': ACTIVE_DELIVERY_STATUS,
            'payment_status__name__in': ACTIVE_PAYMENT_STATUS,
        }

        active_orders = client_orders.filter(**active_query).count()
        active_sales = total_sales.filter(**active_query).count()

        completed_sales = (
            total_sales
            .filter(
                delivery_status__name='Delivered',
                payment_status__name='Paid'
            )
        )

        total_profit = sum(sale.net_profit for sale in completed_sales)

        return Response({'total_items': total_items_quantities,
                         'total_sales': total_sales.count(),
                         'active_sales_orders': active_sales + active_orders,
                         'total_profit': total_profit},
                         status=status.HTTP_200_OK)


class GetSalesStatus(CreatedByUserMixin, generics.GenericAPIView):
    """Returns Sales data for dashboard charts"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        date_range_q = request.GET.get('period', 'week')
        today = date.today()
        year = today.year
        month = today.month

        if date_range_q == 'week':
            DAY_NAMES = {
                1: 'Mon',
                2: 'Tue',
                3: 'Wed',
                4: 'Thu',
                5: 'Fri',
                6: 'Sat',
                7: 'Sun',
            }
            categories = list(DAY_NAMES.values())
            start_of_week = datetime.combine(
                datetime.today() - timedelta(days=today.weekday()),
                time.min
            )
            end_of_week = datetime.combine(start_of_week + timedelta(days=6),
                                           time.max)

            date_range = (start_of_week.strftime("%d.%m.%Y") 
                          + ' - ' + end_of_week.strftime("%d.%m.%Y"))
            initial_days_map = {i: 0 for i in range(1, 8)}
            date_type_query = {'day': ExtractIsoWeekDay('created_at')}

            created_at_range = [
                make_aware_datetime(start_of_week),
                make_aware_datetime(end_of_week)
            ]

        else:
            _, last_day = calendar.monthrange(year, month)

            categories = [
                date(year, month, day).strftime("%d.%m.%Y")
                for day in range(1, last_day + 1)
            ]

            start_of_month = make_aware_datetime(
                datetime.combine(datetime(year, month, 1), time.min)
            )
            end_of_month = make_aware_datetime(
                datetime.combine(datetime(year, month, last_day), time.max)
            )

            date_range = categories[0] + ' - ' + categories[-1] 
            initial_days_map = {i: 0 for i in range(1, last_day + 1)}
            date_type_query = {'day': ExtractDay('created_at')}

            created_at_range = [start_of_month, end_of_month]

        sales = Sale.objects.filter(
            created_by=user,
            created_at__range=created_at_range
        )

        client_orders = ClientOrder.objects.filter(
            created_by=user,
            created_at__range=created_at_range
        )

        # Completed sales and failed sales - orders query
        completed_query = {
            'delivery_status__name': 'Delivered',
            'payment_status__name': 'Paid'
        }

        failed_query = (Q(delivery_status__name__in=FAILED_STATUS) | 
                        Q(payment_status__name__in=FAILED_STATUS))

        # Completed sales per day
        completed_sales_per_day = records_per_day(
            completed_query,
            initial_days_map,
            date_type_query,
            sales
        )

        # Failed sales orders per day
        failed_sales_orders_per_day = records_per_day(
            failed_query,
            initial_days_map,
            date_type_query,
            sales,
            client_orders
        )

        series = [
            {
                'name': 'Failed Sales - Orders',
                'data': list(failed_sales_orders_per_day.values())
            },
            {
                'name': 'Completed Sales',
                'data': list(completed_sales_per_day.values())
            }
        ]

        return Response({'series': series,
                         'date_range': date_range,
                         'categories': categories},
                         status=status.HTTP_200_OK)
