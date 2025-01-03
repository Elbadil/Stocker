from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Q
from ..auth import TokenVersionAuthentication
from apps.inventory.models import Item
from apps.client_orders.models import ClientOrder
from apps.sales.models import Sale
from utils.views import CreatedByUserMixin
from ..utils import (generate_filter_info, records_per_day,
                     revenue_per_day)
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
    """Returns Sales data for dashboard's Sales status chart"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        period_q = request.GET.get('period', 'week')

        result = generate_filter_info(period_q)
        if isinstance(result, Response):
            return result

        filter_info = result

        sales = Sale.objects.filter(
            created_by=user,
            created_at__range=filter_info['created_at_range']
        )

        client_orders = ClientOrder.objects.filter(
            created_by=user,
            created_at__range=filter_info['created_at_range']
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
            filter_info['initial_days_map'],
            filter_info['date_type_query'],
            sales
        )

        # Failed sales orders per day
        failed_sales_orders_per_day = records_per_day(
            failed_query,
            filter_info['initial_days_map'],
            filter_info['date_type_query'],
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
                         'date_range': filter_info['date_range'],
                         'categories': filter_info['categories']},
                         status=status.HTTP_200_OK)


class GetSalesRevenue(CreatedByUserMixin, generics.GenericAPIView):
    """Returns Sales data for dashboard's Sales Profit chart"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Sale.objects.all()

    def get(self, request, *args, **kwargs):
        period_q = request.GET.get('period', 'week')

        result = generate_filter_info(period_q)
        if isinstance(result, Response):
            return result

        filter_info = result

        sales = self.get_queryset()
        completed_sales = (
            sales
            .filter(
                delivery_status__name='Delivered',
                payment_status__name='Paid',
                created_at__range=filter_info['created_at_range']
            )
        )

        # Completed sales revenue per day
        sales_revenue_per_day = revenue_per_day(
            completed_sales,
            filter_info['date_type_query'],
            filter_info['initial_revenue_per_day_map']
        )

        # Extract costs and profits
        costs, profits = zip(*(
            (value['cost'], value['profit'])
            for value in sales_revenue_per_day.values()
        ))
        costs_list = list(costs)
        profits_list = list(profits)

        series = [
            {
                'name': 'Cost',
                'data': costs_list
            },
            {
                'name': 'Profit',
                'data': profits_list
            }
        ]

        total_revenue = sum(costs_list + profits_list)

        return Response({'series': series,
                         'date_range': filter_info['date_range'],
                         'categories': filter_info['categories'],
                         'total_revenue': total_revenue},
                         status=status.HTTP_200_OK)
