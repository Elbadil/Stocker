from rest_framework.pagination import CursorPagination


class CustomCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'
    page_size_query_param = 'page_size'
    max_page_size = 100
