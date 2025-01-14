from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Q, F, Value, CharField
from django.db.models.functions import Concat
from django.conf import settings
from ..auth import TokenVersionAuthentication
from ..models import User, Activity
from ..serializers import ActivitySerializer
from apps.inventory.models import Item
from apps.client_orders.models import ClientOrder
from apps.sales.models import Sale, SoldItem
from ..utils import (generate_filter_info, records_per_day,
                     revenue_per_day)
from utils.status import (ACTIVE_DELIVERY_STATUS,
                          ACTIVE_PAYMENT_STATUS,
                          FAILED_STATUS)
from typing import Union


class DashboardAPIView(generics.GenericAPIView):
    """Return necessary data related to the user's dashboard"""
    authentication_classes = (TokenVersionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs) -> Response:
        user = request.user
        info = request.GET.get('info', None)
        period_q = request.GET.get('period', 'week')
        limit_q = request.GET.get('limit', 5)

        if not info:
            return Response(
                {'error': 'info parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if info == 'general':
            return self.get_general_info(user)

        elif info == 'sales-status':
            return self.get_sales_status_info(user, period_q)
        
        elif info == 'sales-revenue':
            return self.get_sales_revenue_info(user, period_q)
        
        elif info == 'top-selling-items':
            return self.get_top_selling_items_info(request, user, limit_q)
        
        elif info == 'recent-activities':
            return self.get_recent_activities_info(request, user, limit_q)

        else:
            return Response(
                {'error': 'Invalid info parameter.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_general_info(self, user: User) -> Response:
        """
        Returns dashboard's general info:
            - Total Profit
            - Total Sales
            - Total Active Sales - Orders
            - Total Items in inventory
        """
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

    def get_sales_status_info(self, user: User, period_q: str) -> Response:
        """
        Returns sales status info with week and month as period options
        """
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

    def get_sales_revenue_info(self, user: User, period_q: str) -> Response:
        """
        Returns sales revenue info with week and month as period options
        """
        result = generate_filter_info(period_q)
        if isinstance(result, Response):
            return result

        filter_info = result

        completed_sales = Sale.objects.filter(
            created_by=user,
            delivery_status__name='Delivered',
            payment_status__name='Paid',
            created_at__range=filter_info['created_at_range']
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

    def get_top_selling_items_info(
        self,
        request,
        user: User,
        limit_q: Union[int, str]
    ) -> Response:
        """
        Returns top selling items based on completed sales' sold quantity
        """
        try:
            limit = int(limit_q)
        except ValueError:
            return Response(
                {'error': 'limit parameter must be a number.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        completed_sales = Sale.objects.filter(
            created_by=user,
            delivery_status__name='Delivered',
            payment_status__name='Paid',
        )

        sold_items = SoldItem.objects.filter(sale__in=completed_sales)
        top_selling_items = (
            sold_items
            .values(name=F('item__name'))
            .annotate(
                picture=Concat(
                    Value(request.build_absolute_uri(settings.MEDIA_URL)),
                    F('item__picture'),
                    output_field=CharField()
                ),
                total_quantity=Sum('sold_quantity'),
                total_profit=(
                    Sum(F('sold_quantity') * F('sold_price')) -
                    Sum(F('sold_quantity') * F('item__price'))
                ),
                total_revenue=Sum(F('sold_quantity') * F('sold_price')),
            )
            .order_by('-total_quantity')[:limit]
        )

        return Response(top_selling_items, status=status.HTTP_200_OK)

    def get_recent_activities_info(
        self,
        request,
        user: User,
        limit_q: Union[int, str]
    ) -> Response:
        """"""
        try:
            limit = int(limit_q)
        except ValueError:
            return Response(
                {'error': 'limit parameter must be a number.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        activities = Activity.objects.filter(user=user)[:limit]
        serializer = ActivitySerializer(
            activities,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
